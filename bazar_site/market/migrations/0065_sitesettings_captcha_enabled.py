from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("market", "0064_support_purchase_request_link"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="captcha_enabled",
            field=models.BooleanField(
                default=False,
                help_text="Если выключено — проверка reCAPTCHA на входе/регистрации будет отключена.",
                verbose_name="Включить CAPTCHA",
            ),
        ),
    ]

