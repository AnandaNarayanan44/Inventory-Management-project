from django.db import models

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    gst = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    description = models.TextField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)

class Supplier(models.Model):
    name=models.CharField(max_length=100)
    contact_number=models.CharField(max_length=20,blank=True)
    email=models.EmailField(blank=True)
    address=models.TextField(blank=True,null=True)
