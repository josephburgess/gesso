from django.db import migrations


def keep_newest_first(apps, schema_editor):
    Artwork = apps.get_model('artworks', 'Artwork')
    for position, artwork in enumerate(Artwork.objects.order_by('-year', 'title')):
        artwork.position = position
        artwork.save(update_fields=['position'])


class Migration(migrations.Migration):
    dependencies = [
        ('artworks', '0018_schema_work_order'),
    ]

    operations = [
        migrations.RunPython(keep_newest_first, migrations.RunPython.noop),
    ]
