from django.contrib import admin
from .models import Product, Supplier, StockEntry
# Register your models here.

admin.site.register(Product)
admin.site.register(Supplier)
admin.site.register(StockEntry) 