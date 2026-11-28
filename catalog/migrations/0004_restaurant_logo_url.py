from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0003_restaurant_delivery_policies")]

    operations = [
        migrations.AddField(
            model_name="restaurant",
            name="logo_url",
            field=models.URLField(blank=True, verbose_name="Логотип"),
        ),
    ]
