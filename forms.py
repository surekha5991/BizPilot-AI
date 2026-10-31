from django import forms
from .models import Product, Sale

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "price", "stock", "low_stock_limit"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Organic rice"}),
            "category": forms.TextInput(attrs={"placeholder": "e.g. Grocery"}),
            "price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "stock": forms.NumberInput(attrs={"min": "0"}),
            "low_stock_limit": forms.NumberInput(attrs={"min": "0"}),
        }

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ["product", "quantity"]
        widgets = {"quantity": forms.NumberInput(attrs={"min": "1"})}
