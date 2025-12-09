from django.contrib import admin
from .models import (
    Product,
    Supplier,
    Warehouse,
    InventoryItem,
    StockEntry,
    StockReduction,
    Sale,
    SaleItem,
)


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("product", "warehouse", "quantity_on_hand", "low_stock_threshold")
    list_filter = ("warehouse", "product__category")
    search_fields = ("product__name", "warehouse__name")


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "customer_name", "sale_date", "total_amount")
    search_fields = ("invoice_number", "customer_name")
    inlines = [SaleItemInline]


admin.site.register(Product)
admin.site.register(Supplier)
admin.site.register(Warehouse)
admin.site.register(StockEntry)
admin.site.register(StockReduction)