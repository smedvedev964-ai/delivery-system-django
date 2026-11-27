from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Restaurant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160, unique=True, verbose_name="Название ресторана")),
                ("slug", models.SlugField(max_length=180, unique=True, verbose_name="Адрес страницы")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("cuisine", models.CharField(db_index=True, max_length=80, verbose_name="Кухня")),
                ("address", models.CharField(blank=True, max_length=255, verbose_name="Адрес")),
                ("image_url", models.URLField(blank=True, verbose_name="Фотография ресторана")),
                ("rating", models.DecimalField(decimal_places=1, default=0, max_digits=2, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)], verbose_name="Рейтинг")),
                ("rating_count", models.PositiveIntegerField(default=0, verbose_name="Количество оценок")),
                ("delivery_min", models.PositiveSmallIntegerField(default=30, verbose_name="Минимальное время доставки")),
                ("delivery_max", models.PositiveSmallIntegerField(default=45, verbose_name="Максимальное время доставки")),
                ("delivery_fee", models.DecimalField(decimal_places=2, default=0, max_digits=8, validators=[django.core.validators.MinValueValidator(0)], verbose_name="Стоимость доставки")),
                ("is_active", models.BooleanField(default=True, verbose_name="Работает")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Добавлен")),
            ],
            options={"ordering": ["-rating", "name"], "verbose_name": "Ресторан", "verbose_name_plural": "Рестораны"},
        ),
        migrations.AddField(
            model_name="product",
            name="restaurant",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="products", to="catalog.restaurant", verbose_name="Ресторан"),
        ),
        migrations.AddField(
            model_name="product",
            name="image_url",
            field=models.URLField(blank=True, verbose_name="Ссылка на фотографию"),
        ),
    ]
