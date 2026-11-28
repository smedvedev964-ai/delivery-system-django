from decimal import Decimal

from django.db import migrations, models
import django.core.validators


def set_demo_delivery_policies(apps, schema_editor):
    Restaurant = apps.get_model("catalog", "Restaurant")
    policies = {
        "dodo-pizza": ("threshold", "149.00", "999.00"),
        "teremok": ("fixed", "99.00", None),
        "shokoladnitsa": ("fixed", "149.00", None),
        "mybox": ("threshold", "199.00", "1200.00"),
        "kroshka-kartoshka": ("fixed", "129.00", None),
        "vkusno-i-tochka": ("fixed", "149.00", None),
        "rostics": ("fixed", "149.00", None),
        "sushi-wok": ("threshold", "179.00", "900.00"),
    }
    for slug, (policy, fee, threshold) in policies.items():
        Restaurant.objects.filter(slug=slug).update(
            delivery_policy=policy,
            delivery_fee=Decimal(fee),
            free_delivery_threshold=Decimal(threshold) if threshold else None,
        )


class Migration(migrations.Migration):
    dependencies = [("catalog", "0002_restaurants_and_product_images")]

    operations = [
        migrations.AddField(
            model_name="restaurant",
            name="delivery_policy",
            field=models.CharField(
                choices=[
                    ("fixed", "Фиксированная стоимость"),
                    ("free", "Бесплатная доставка"),
                    ("threshold", "Бесплатно от суммы заказа"),
                ],
                default="fixed",
                max_length=12,
                verbose_name="Условия доставки",
            ),
        ),
        migrations.AlterField(
            model_name="restaurant",
            name="delivery_fee",
            field=models.DecimalField(
                decimal_places=2,
                default=149,
                max_digits=8,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name="Стоимость доставки",
            ),
        ),
        migrations.AddField(
            model_name="restaurant",
            name="free_delivery_threshold",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name="Порог бесплатной доставки",
            ),
        ),
        migrations.RunPython(set_demo_delivery_policies, migrations.RunPython.noop),
    ]
