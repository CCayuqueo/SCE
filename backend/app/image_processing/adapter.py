import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import BoundedSemaphore

from pydantic import ValidationError

from app.core.config import Settings
from app.core.errors import ApiError
from app.image_processing.schemas import ParserResult
from app.image_processing.validators import invalid_image, validate_image
from app.schedules.schemas import ScheduleCell

BACKEND = Path(__file__).resolve().parents[2]
DAYS = {
    name: index
    for index, name in enumerate(
        ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"), 1
    )
}
BLOCKS = {f"{2 * index - 1}-{2 * index}": index for index in range(1, 11)}
OCCUPIED = {"inscrita", "tope", "pre-inscrita"}


def normalize_result(payload: str, size: tuple[int, int]) -> list[ScheduleCell]:
    try:
        result = ParserResult.model_validate_json(payload)
    except ValidationError as error:
        raise invalid_image() from error
    if (result.dimensiones.ancho, result.dimensiones.alto) != size:
        raise invalid_image()

    occupied = set()
    for entry in result.horarios:
        day = DAYS.get(entry.dia.strip().lower())
        block = BLOCKS.get(entry.bloque.strip())
        if (
            day is None
            or block is None
            or entry.estado not in OCCUPIED
            or (day, block) in occupied
        ):
            raise invalid_image()
        occupied.add((day, block))
    # El parser solo devuelve un resultado tras recorrer todos los límites de la grilla.
    return [
        ScheduleCell(day=day, block=block, is_occupied=(day, block) in occupied)
        for day in range(1, 8)
        for block in range(1, 11)
    ]


class ImageProcessor:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.slots = BoundedSemaphore(settings.image_processing_concurrency)

    def process(self, data: bytes) -> list[ScheduleCell]:
        suffix, size = validate_image(data, self.settings.max_image_pixels)
        if not self.slots.acquire(blocking=False):
            raise ApiError(
                503,
                "IMAGE_PROCESSOR_BUSY",
                "El procesador está ocupado. Intenta de nuevo.",
            )
        try:
            with TemporaryDirectory(prefix="src-schedule-") as directory:
                image = Path(directory) / f"capture{suffix}"
                image.write_bytes(data)
                timeout = self.settings.image_processing_timeout_seconds
                try:
                    result = subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "app.image_processing.worker",
                            str(image),
                            str(timeout),
                        ],
                        cwd=BACKEND,
                        env={
                            "LANG": "C.UTF-8",
                            "OPENBLAS_NUM_THREADS": "1",
                            "OMP_NUM_THREADS": "1",
                            "OPENCV_FOR_THREADS_NUM": "1",
                            "OPENCV_IO_MAX_IMAGE_PIXELS": str(
                                self.settings.max_image_pixels
                            ),
                            "PYTHONDONTWRITEBYTECODE": "1",
                        },
                        stdin=subprocess.DEVNULL,
                        capture_output=True,
                        encoding="utf-8",
                        timeout=timeout,
                        shell=False,
                        check=False,
                    )
                except subprocess.TimeoutExpired as error:
                    raise ApiError(
                        422,
                        "IMAGE_PROCESSING_TIMEOUT",
                        "La captura tardó demasiado en procesarse.",
                    ) from error
                if result.returncode == 2:
                    raise invalid_image()
                if result.returncode != 0:
                    raise ApiError(
                        503,
                        "IMAGE_PROCESSOR_FAILED",
                        "No se pudo ejecutar el procesador de horarios.",
                    )
                return normalize_result(result.stdout, size)
        finally:
            self.slots.release()
