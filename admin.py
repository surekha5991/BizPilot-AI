from django.contrib import admin
from .models import Product, Sale

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "low_stock_limit")
    search_fields = ("name", "category")

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("product", "quantity", "unit_price", "sold_at")
    list_filter = ("sold_at",)
