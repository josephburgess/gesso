import io
from typing import IO, NamedTuple

from PIL import Image, ImageOps

WIDTHS = (480, 960, 1600, 2400)


class Variant(NamedTuple):
    width: int
    height: int
    data: bytes


def webp_variants(file: IO[bytes]) -> list[Variant]:
    with Image.open(file) as source:
        icc = source.info.get('icc_profile')
        image = ImageOps.exif_transpose(source).convert('RGB')

    variants = []
    for width in sorted({min(w, image.width) for w in WIDTHS}):
        height = round(image.height * width / image.width)
        buffer = io.BytesIO()
        image.resize((width, height), Image.Resampling.LANCZOS).save(buffer, 'WEBP', quality=82, icc_profile=icc)
        variants.append(Variant(width, height, buffer.getvalue()))
    return variants
