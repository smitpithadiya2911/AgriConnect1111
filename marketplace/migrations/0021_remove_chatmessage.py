from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0020_crop_rating'),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS marketplace_chatmessage;",
            reverse_sql="",  # irreversible - table data is gone
        ),
    ]
