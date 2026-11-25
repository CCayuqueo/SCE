from struct import unpack_from

from app.core.errors import ApiError

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SOF = {
    0xC0,
    0xC1,
    0xC2,
    0xC3,
    0xC5,
    0xC6,
    0xC7,
    0xC9,
    0xCA,
    0xCB,
    0xCD,
    0xCE,
    0xCF,
}


def invalid_image() -> ApiError:
    return ApiError(
        422,
        "INVALID_IMAGE",
        "La imagen está dañada o no contiene un horario compatible.",
    )


def jpeg_dimensions(data: bytes) -> tuple[int, int]:
    offset = 2
    while offset + 4 <= len(data) and data[offset] == 0xFF:
        offset += 1
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset + 3 > len(data):
            break
        marker = data[offset]
        size = int.from_bytes(data[offset + 1 : offset + 3], "big")
        if marker in {0xDA, 0xD9} or size < 2 or offset + 1 + size > len(data):
            break
        if marker in JPEG_SOF and size >= 8:
            height, width = unpack_from(">HH", data, offset + 4)
            return width, height
        offset += 1 + size
    raise invalid_image()


def validate_image(data: bytes, max_pixels: int) -> tuple[str, tuple[int, int]]:
    if data.startswith(PNG_SIGNATURE):
        if len(data) < 33 or data[8:16] != b"\x00\x00\x00\x0dIHDR":
            raise invalid_image()
        width, height = unpack_from(">II", data, 16)
        suffix = ".png"
    elif data.startswith(b"\xff\xd8\xff"):
        width, height = jpeg_dimensions(data)
        suffix = ".jpg"
    else:
        raise ApiError(
            415,
            "UNSUPPORTED_IMAGE_FORMAT",
            "La captura debe estar en formato PNG o JPEG.",
        )
    if not width or not height:
        raise invalid_image()
    if width * height > max_pixels:
        raise ApiError(
            413, "IMAGE_TOO_LARGE", "La captura excede el límite de píxeles."
        )
    return suffix, (width, height)
