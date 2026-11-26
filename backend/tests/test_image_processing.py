import json
import subprocess
from itertools import pairwise
from pathlib import Path

import cv2
import pytest

from app.core.config import Settings
from app.core.errors import ApiError
from app.image_processing.adapter import ImageProcessor, normalize_result
from app.image_processing.validators import validate_image

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = json.loads(
    (Path(__file__).parent / "fixtures/schedule_reference.json").read_text()
)
SAMPLE = ROOT / "images" / next(iter(REFERENCE))


@pytest.mark.parametrize("corruption", ["jpeg_segment", "png_width"])
def test_rejects_broken_image_headers_before_decoding(corruption):
    if corruption == "jpeg_segment":
        data = b"\xff\xd8\xff\xe0\x00\x01\x00"
    else:
        sample = SAMPLE.read_bytes()
        data = sample[:16] + bytes(4) + sample[20:]
    with pytest.raises(ApiError) as error:
        validate_image(data, 12_000_000)
    assert error.value.status == 422


def processor():
    return ImageProcessor(Settings(database_url="postgresql+psycopg:///unused"))


@pytest.mark.parametrize(("filename", "expected"), REFERENCE.items())
def test_worker_matches_occupied_coordinates_in_all_reference_images(
    filename, expected
):
    cells = processor().process((ROOT / "images" / filename).read_bytes())
    assert len(cells) == 70
    assert [
        {"day": c.day, "block": c.block} for c in cells if c.is_occupied
    ] == expected


def test_jpeg_and_unsupported_dimensions():
    image = cv2.imread(str(SAMPLE))
    success, jpeg = cv2.imencode(
        ".jpg",
        image,
        [
            cv2.IMWRITE_JPEG_QUALITY,
            100,
            cv2.IMWRITE_JPEG_SAMPLING_FACTOR,
            cv2.IMWRITE_JPEG_SAMPLING_FACTOR_444,
        ],
    )
    assert success
    cells = processor().process(jpeg.tobytes())
    assert [
        {"day": c.day, "block": c.block} for c in cells if c.is_occupied
    ] == REFERENCE[SAMPLE.name]
    with pytest.raises(ApiError) as error:
        validate_image(SAMPLE.read_bytes(), 100)
    assert error.value.status == 413


def test_complete_empty_grid_is_distinguished_from_incomplete_grid():
    image = cv2.imread(str(SAMPLE))
    # Primera captura: el interior semanal excluye el encabezado y la leyenda.
    bounds = [79, 168, 256, 345, 434, 522, 611, 700]
    for left, right in pairwise(bounds):
        for row in range(10):
            top = 27 + row * 21
            image[top + 1 : top + 21, left + 1 : right] = 255
    assert not any(
        cell.is_occupied
        for cell in processor().process(cv2.imencode(".png", image)[1].tobytes())
    )
    with pytest.raises(ApiError, match="no contiene un horario compatible"):
        processor().process(cv2.imencode(".png", image[:150])[1].tobytes())


def test_rejects_invalid_json_coordinate_and_duplicate():
    with pytest.raises(ApiError):
        normalize_result("invalid json", (1, 1))
    valid = {"dia": "Lunes", "bloque": "1-2", "estado": "inscrita"}
    for rows in ([valid, valid], [{**valid, "dia": "no existe"}]):
        with pytest.raises(ApiError):
            normalize_result(
                json.dumps({"dimensiones": {"ancho": 1, "alto": 1}, "horarios": rows}),
                (1, 1),
            )


def test_timeout_cleans_temporaries_and_releases_slot(monkeypatch):
    adapter = processor()
    path = None

    def timeout(args, **kwargs):
        nonlocal path
        path = Path(args[-2])
        assert path.is_file()
        raise subprocess.TimeoutExpired(args, kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(ApiError) as error:
        adapter.process(SAMPLE.read_bytes())
    assert error.value.code == "IMAGE_PROCESSING_TIMEOUT"
    assert not path.parent.exists()
    assert adapter.slots.acquire(blocking=False)
