from django.contrib import admin
from django.urls import path
from InventoryApp import views

urlpatterns = [
    path('',views.index,name='index page'),
    path('/productIndexPage',views.productPage,name='product page')
]