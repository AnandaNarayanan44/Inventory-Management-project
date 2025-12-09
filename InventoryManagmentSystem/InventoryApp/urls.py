from django.contrib import admin
from django.urls import path
from InventoryApp import views

urlpatterns = [
    path('',views.index,name='index page'),
    path('productIndexPage',views.productPage,name='product page'),
    path('productCreation',views.productCreate,name='createProduct'),
    path('productEdit/<int:pk>',views.productEdit,name='productEdit'),
    path('productDelete/<int:pk>/', views.productDelete, name='product delete'),
    path('uplodeCsv',views.uplodeCsv,name='uplodeCsv'),
    path('exportCsv', views.exportCsv, name='exportCsv'),
    path('inventory',views.inventory,name='inventory'),
    path('addStock',views.stockAdding,name='addStock'),
    path('reduceStock',views.stockReducing,name='reduceStock'),
    path('addSupplier',views.addSupplier,name='addSupplier'),
    path("predict-expiry/", views.expiry_risk_view, name="predict_expiry"),
    path("billing", views.billing, name="billing"),
    path("inventory/reports", views.inventory_reports, name="inventory_reports"),
    path("warehouses", views.warehouse_management, name="warehouse_management"),
    path("inventory/item/<int:pk>/edit", views.edit_inventory_item, name="editInventoryItem"),
    path("inventory/item/<int:pk>/delete", views.delete_inventory_item, name="deleteInventoryItem"),
    path("inventory/stock-level/", views.stock_level_api, name="stock_level_api"),
]