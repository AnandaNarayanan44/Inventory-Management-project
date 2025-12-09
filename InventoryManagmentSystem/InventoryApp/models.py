from django.db import models
from django.utils import timezone


class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    gst = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    description = models.TextField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    name = models.CharField(max_length=120, unique=True)
    location = models.CharField(max_length=255, blank=True)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_items')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='inventory_items')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    quantity_on_hand = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    expiry_date = models.DateField(blank=True, null=True)
    last_restocked = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'warehouse')
        verbose_name = "Inventory Item"
        verbose_name_plural = "Inventory Items"

    def __str__(self):
        return f"{self.product.name} @ {self.warehouse.name}"

    @property
    def is_expired(self):
        return bool(self.expiry_date and self.expiry_date < timezone.now().date())


class StockEntry(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_entries')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock_entries', null=True, blank=True)
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='entries', null=True, blank=True)

    quantity_added = models.PositiveIntegerField()
    expiry_date = models.DateField(null=True, blank=True)
    batch_number = models.CharField(max_length=50, blank=True)
    barcode = models.CharField(max_length=100, unique=True)

    notes = models.TextField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - Added {self.quantity_added}"


class StockReduction(models.Model):
    SALE = 'sale'
    DAMAGE = 'damage'
    EXPIRED = 'expired'
    THEFT = 'theft'
    RETURN = 'return'
    OTHER = 'other'
    REASON_CHOICES = [
        (SALE, 'Sale'),
        (DAMAGE, 'Damage'),
        (EXPIRED, 'Expired'),
        (THEFT, 'Theft'),
        (RETURN, 'Return to Supplier'),
        (OTHER, 'Other'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reductions')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='reductions')
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='reductions', null=True, blank=True)
    sale = models.ForeignKey('Sale', on_delete=models.CASCADE, related_name='reductions', null=True, blank=True)
    quantity_removed = models.PositiveIntegerField()
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    customer_name = models.CharField(max_length=120, blank=True)
    sale_date = models.DateField(default=timezone.now)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, default=SALE)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.quantity_removed} ({self.get_reason_display()})"


class Sale(models.Model):
    invoice_number = models.CharField(max_length=30, unique=True)
    customer_name = models.CharField(max_length=120, blank=True)
    staff_name = models.CharField(max_length=120, blank=True)
    sale_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sale_date', '-created_at']

    def __str__(self):
        return f"Invoice {self.invoice_number}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"
