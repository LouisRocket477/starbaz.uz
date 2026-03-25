from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0052_sitesettings_about_page_body_and_more"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="sellerreview",
            unique_together=set(),
        ),
    ]

