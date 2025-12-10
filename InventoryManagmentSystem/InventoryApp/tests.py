from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Product, Warehouse, InventoryItem, Sale, StaffProfile


class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="admin@example.com", password="Admin@123")
        StaffProfile.objects.create(user=self.user, role=StaffProfile.ROLE_ADMIN)

    def test_login_redirects_to_dashboard(self):
        response = self.client.post(reverse("login"), {"username": "admin@example.com", "password": "Admin@123"})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin_dashboard"), response.headers["Location"])


class BillingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="staff@example.com", password="Staff@123")
        StaffProfile.objects.create(user=self.user, role=StaffProfile.ROLE_STAFF)
        self.client.login(username="staff@example.com", password="Staff@123")
        self.product = Product.objects.create(name="Test Product", category="General", price=10, gst=5)
        self.warehouse = Warehouse.objects.create(name="Main Warehouse")
        InventoryItem.objects.create(product=self.product, warehouse=self.warehouse, quantity_on_hand=10)

    def test_invoice_creation(self):
        payload = {
            "customer_name": "John",
            "staff_name": "Staff",
            "sale_date": "2025-01-01",
            "item_product[]": [str(self.product.id)],
            "item_quantity[]": ["2"],
            "item_price[]": ["10"],
            "item_warehouse[]": [str(self.warehouse.id)],
        }
        response = self.client.post(reverse("billing"), data=payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Sale.objects.count(), 1)
