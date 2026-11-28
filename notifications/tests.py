from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Notification

User = get_user_model()


class NotificationAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner", email="owner@example.test", password="strong-test-password"
        )
        self.other = User.objects.create_user(
            username="other", email="other@example.test", password="strong-test-password"
        )
        self.notification = Notification.objects.create(
            user=self.owner, title="Заказ", message="Статус изменён"
        )

    def test_user_sees_and_marks_only_own_notifications(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("notifications:list")).context["notifications"].count(), 0)
        denied = self.client.post(reverse("notifications:list"), {"notification_id": self.notification.pk})
        self.assertEqual(denied.status_code, 404)
        self.notification.refresh_from_db()
        self.assertFalse(self.notification.is_read)

        self.client.force_login(self.owner)
        response = self.client.post(reverse("notifications:list"), {"notification_id": self.notification.pk})
        self.assertEqual(response.status_code, 302)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)
