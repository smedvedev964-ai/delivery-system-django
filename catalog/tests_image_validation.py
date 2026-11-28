from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image

from .validators import MAX_PRODUCT_IMAGE_SIZE, validate_product_image


class ProductImageValidationTests(SimpleTestCase):
    def test_accepts_valid_png_and_rejects_unsupported_formats(self):
        buffer = BytesIO()
        Image.new("RGB", (2, 2), color="red").save(buffer, format="PNG")
        image = SimpleUploadedFile("dish.png", buffer.getvalue(), content_type="image/png")
        validate_product_image(image)

        gif = SimpleUploadedFile("dish.gif", b"GIF89a", content_type="image/gif")
        with self.assertRaises(ValidationError):
            validate_product_image(gif)

    def test_rejects_images_over_size_limit(self):
        oversized = SimpleUploadedFile(
            "dish.png", b"0" * (MAX_PRODUCT_IMAGE_SIZE + 1), content_type="image/png"
        )
        with self.assertRaises(ValidationError):
            validate_product_image(oversized)
