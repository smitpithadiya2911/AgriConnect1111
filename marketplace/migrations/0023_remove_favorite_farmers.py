from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0021_remove_chatmessage'),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS accounts_buyer_favorite_farmers;",
            reverse_sql="",
        ),
    ]
