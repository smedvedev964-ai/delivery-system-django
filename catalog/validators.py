from PIL import Image, UnidentifiedImageError
from django.core.exceptions import ValidationError


MAX_PRODUCT_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_PRODUCT_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


def validate_product_image(upload):
    if upload.size > MAX_PRODUCT_IMAGE_SIZE:
        raise ValidationError("Изображение блюда должно быть не больше 5 МБ.")

    try:
        upload.seek(0)
        image = Image.open(upload)
        image_format = image.format
        if image.width * image.height > 20_000_000:
            raise ValidationError("Слишком большое разрешение изображения.")
        image.verify()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError, ValueError):
        raise ValidationError("Загрузите корректное изображение в формате JPEG, PNG или WebP.")
    finally:
        upload.seek(0)

    if image_format not in ALLOWED_PRODUCT_IMAGE_FORMATS:
        raise ValidationError("Допустимые форматы изображения: JPEG, PNG и WebP.")
