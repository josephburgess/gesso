from django.db import migrations


def clear_spot_three(apps, schema_editor):
    apps.get_model('artworks', 'Artwork').objects.filter(featured_order=3).update(featured_order=None)


class Migration(migrations.Migration):
    dependencies = [
        ('artworks', '0012_schema_two_home_page_spots'),
    ]

    operations = [
        migrations.RunPython(clear_spot_three, migrations.RunPython.noop),
    ]
