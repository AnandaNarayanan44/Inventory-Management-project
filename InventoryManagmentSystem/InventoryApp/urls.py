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
    path('reduceStock',views.stockReducing,name='reduceStock')

    
]