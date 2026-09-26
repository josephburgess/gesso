from django.db import migrations


def keep_current_studio_photos(apps, schema_editor):
    Artwork = apps.get_model('artworks', 'Artwork')
    ArtworkImage = apps.get_model('artworks', 'ArtworkImage')
    published = Artwork.objects.filter(is_published=True)
    works = [*published.exclude(featured_order=None).order_by('featured_order'), *published.filter(featured_order=None).order_by('-year', 'title')]
    photos = [
        photo
        for work in works
        for photo in ArtworkImage.objects.filter(artwork=work, is_process=True).exclude(variants=[]).order_by('position', 'pk')
    ]
    for position, photo in enumerate(photos[:2]):
        photo.home_position = position
        photo.save(update_fields=['home_position'])


class Migration(migrations.Migration):
    dependencies = [
        ('artworks', '0014_schema_pending_images_and_home_photos'),
    ]

    operations = [
        migrations.RunPython(keep_current_studio_photos, migrations.RunPython.noop),
    ]
