import io
from typing import IO

from django.core.files.base import ContentFile
from django.db.models import Max
from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageOps

from gesso.artworks.models import Artwork, ArtworkImage, FrameColour, RoomScene

FRAME_CM = 2
FRAME_HEX = {
    FrameColour.BLACK: '#1c1c1c',
    FrameColour.WHITE: '#f2f0eb',
    FrameColour.OAK: '#b58a5a',
    FrameColour.WALNUT: '#5c3e2a',
}


def _open(file: IO[bytes]) -> Image.Image:
    with Image.open(file) as image:
        return ImageOps.exif_transpose(image).convert('RGB')


def _frame(art: Image.Image, width: int, colour: FrameColour) -> Image.Image:
    rgb = ImageColor.getrgb(FRAME_HEX[colour])
    edge = tuple(round(c * 0.65 + 128 * 0.35) for c in rgb)
    framed = ImageOps.expand(art, border=width, fill=rgb)
    ImageDraw.Draw(framed).rectangle((width - 1, width - 1, width + art.width, width + art.height), outline=edge)
    return framed


def render_wall_view(source: IO[bytes], scene: RoomScene, width_mm: int, height_mm: int, colour: FrameColour) -> bytes:
    px_per_cm = float(scene.px_per_cm)
    with scene.photo.open('rb') as photo:
        room = _open(photo).convert('RGBA')

    size = (round(width_mm / 10 * px_per_cm), round(height_mm / 10 * px_per_cm))
    framed = _frame(_open(source).resize(size, Image.Resampling.LANCZOS), round(FRAME_CM * px_per_cm), colour)

    x = round(room.width * float(scene.anchor_x) / 100 - framed.width / 2)
    y = round(room.height * float(scene.anchor_y) / 100 - framed.height / 2)
    if x < 0 or y < 0 or x + framed.width > room.width or y + framed.height > room.height:
        raise ValueError('This work is too large for that scene.')

    shadow = Image.new('RGBA', room.size, (0, 0, 0, 0))
    dx, dy = round(0.2 * px_per_cm), round(0.5 * px_per_cm)
    ImageDraw.Draw(shadow).rectangle((x + dx, y + dy, x + dx + framed.width, y + dy + framed.height), fill=(0, 0, 0, 90))
    room.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(0.8 * px_per_cm)))
    room.paste(framed, (x, y))

    buffer = io.BytesIO()
    room.convert('RGB').save(buffer, 'JPEG', quality=90)
    return buffer.getvalue()


def generate_wall_view(artwork: Artwork, scene: RoomScene, colour: FrameColour) -> ArtworkImage:
    cover = artwork.cover
    if cover is None:
        raise ValueError('Add an image of the finished work first.')
    with cover.original.open('rb') as source:
        data = render_wall_view(source, scene, artwork.width_mm, artwork.height_mm, colour)

    for old in artwork.images.filter(scene=scene):
        old.delete_files()
        old.delete()

    last = artwork.images.aggregate(last=Max('position'))['last']
    image = ArtworkImage(
        artwork=artwork,
        scene=scene,
        original=ContentFile(data, name=f'{artwork.slug}-wall.jpg'),
        alt=f'{artwork.title} hanging on a wall',
        position=0 if last is None else last + 1,
    )
    image.save()
    return image
