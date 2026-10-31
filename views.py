from datetime import timedelta
from decimal import Decimal
from django.contrib import messages
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Product, Sale
from .forms import ProductForm, SaleForm

def dashboard(request):
    products = Product.objects.all().order_by("name")
    sales = Sale.objects.select_related("product")
    revenue_expr = ExpressionWrapper(F("quantity") * F("unit_price"), output_field=DecimalField(max_digits=12, decimal_places=2))
    total_revenue = sales.aggregate(total=Sum(revenue_expr))["total"] or Decimal("0.00")
    recent_sales = sales.order_by("-sold_at")[:6]
    low_stock = products.filter(stock__lte=F("low_stock_limit"))
    context = {
        "product_count": products.count(),
        "sale_count": sales.count(),
        "total_revenue": total_revenue,
        "low_stock": low_stock,
        "recent_sales": recent_sales,
    }
    return render(request, "core/dashboard.html", context)

def products(request):
    return render(request, "core/products.html", {"products": Product.objects.all().order_by("name")})

def product_add(request):
    form = ProductForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Product added successfully.")
        return redirect("products")
    return render(request, "core/product_form.html", {"form": form, "heading": "Add product"})

def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        form.save()
        messages.success(request, "Product updated.")
        return redirect("products")
    return render(request, "core/product_form.html", {"form": form, "heading": "Edit product"})

def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted.")
    return redirect("products")

def sale_add(request):
    form = SaleForm(request.POST or None)
    form.fields["product"].queryset = Product.objects.order_by("name")
    if form.is_valid():
        sale = form.save(commit=False)
        product = sale.product
        if sale.quantity > product.stock:
            form.add_error("quantity", f"Only {product.stock} units are available.")
        else:
            sale.unit_price = product.price
            product.stock -= sale.quantity
            product.save(update_fields=["stock"])
            sale.save()
            messages.success(request, "Sale recorded and stock updated.")
            return redirect("dashboard")
    return render(request, "core/sale_form.html", {"form": form})

def assistant(request):
    products = Product.objects.all()
    sales = Sale.objects.select_related("product")
    revenue_expr = ExpressionWrapper(F("quantity") * F("unit_price"), output_field=DecimalField(max_digits=12, decimal_places=2))
    revenue = sales.aggregate(total=Sum(revenue_expr))["total"] or Decimal("0.00")
    top = (sales.values("product__name").annotate(units=Sum("quantity")).order_by("-units").first())
    low = list(products.filter(stock__lte=F("low_stock_limit")).order_by("stock")[:5])
    insights = []
    if not products.exists():
        insights.append("Add your first product to start tracking inventory and sales.")
    if low:
        names = ", ".join(f"{p.name} ({p.stock} left)" for p in low)
        insights.append(f"Restock attention: {names}. These products are at or below their low-stock limits.")
    else:
        insights.append("No products are currently below their low-stock limits.")
    if top:
        insights.append(f"Your best-selling product by units recorded is {top['product__name']} ({top['units']} units).")
    else:
        insights.append("No sales have been recorded yet. Record sales to discover your best-selling products.")
    insights.append(f"Recorded revenue so far is ₹{revenue:.2f}. Compare this with your costs before making pricing decisions.")
    question = request.POST.get("question", "").strip() if request.method == "POST" else ""
    answer = None
    if question:
        q = question.lower()
        if any(word in q for word in ["low", "stock", "restock"]):
            answer = insights[1]
        elif any(word in q for word in ["top", "best", "popular", "sell"]):
            answer = insights[2]
        elif any(word in q for word in ["revenue", "sales", "income"]):
            answer = insights[3]
        else:
            answer = "Here is a summary based on your current business data: " + " ".join(insights)
    return render(request, "core/assistant.html", {"insights": insights, "question": question, "answer": answer})
