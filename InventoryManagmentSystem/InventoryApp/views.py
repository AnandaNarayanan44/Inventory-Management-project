from decimal import Decimal, ROUND_HALF_UP
import csv
import io
import os
from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum, F, Count
from django.http import Http404, FileResponse, HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone

from xhtml2pdf import pisa

from ml.expiry_predict import predict_expiry_risk
from ml.demand_predict import predict_all_products_demand
from .models import (
    InventoryItem,
    MLModelArtifact,
    Product,
    Sale,
    SaleItem,
    StaffProfile,
    StockEntry,
    StockReduction,
    Supplier,
    Warehouse,
)


def _generate_invoice_number():
    return timezone.now().strftime("INV%Y%m%d%H%M%S")


TWO_PLACES = Decimal("0.01")


def ensure_profile(user: User) -> StaffProfile:
    profile, _ = StaffProfile.objects.get_or_create(
        user=user,
        defaults={
            "role": StaffProfile.ROLE_ADMIN if user.is_superuser else StaffProfile.ROLE_STAFF
        },
    )
    return profile


def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")
            profile = ensure_profile(request.user)
            if not profile.active or profile.role not in allowed_roles:
                messages.error(request, "You do not have permission to access this page.")
                return redirect("index page")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def seed_default_users():
    """Create default admin and staff accounts for quick start."""
    admin_email = "admin@example.com"
    staff_email = "staff@example.com"

    if not User.objects.filter(username=admin_email).exists():
        admin_user = User.objects.create_superuser(
            username=admin_email, email=admin_email, password="Admin@123"
        )
        ensure_profile(admin_user)

    if not User.objects.filter(username=staff_email).exists():
        staff_user = User.objects.create_user(
            username=staff_email, email=staff_email, password="Staff@123"
        )
        ensure_profile(staff_user)


def login_view(request):
    seed_default_users()

    if request.user.is_authenticated:
        return redirect("index page")

    if request.method == "POST":
        username_or_email = request.POST.get("username")
        password = request.POST.get("password")

        username = username_or_email
        user_by_email = User.objects.filter(email=username_or_email).first()
        if user_by_email:
            username = user_by_email.username

        user = authenticate(request, username=username, password=password)
        if user is not None:
            profile = ensure_profile(user)
            if not profile.active:
                messages.error(request, "Your account is deactivated.")
                return redirect("login")
            login(request, user)
            profile.last_login_at = timezone.now()
            profile.save(update_fields=["last_login_at"])
            if profile.role == StaffProfile.ROLE_ADMIN:
                return redirect("admin_dashboard")
            return redirect("billing")
        messages.error(request, "Invalid credentials.")

    return render(request, "auth_login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def index(request):
    profile = ensure_profile(request.user)
    products_count = Product.objects.filter(active=True).count()
    low_stock_count = (
        InventoryItem.objects.filter(quantity_on_hand__lte=F("low_stock_threshold")).count()
    )
    today = timezone.now().date()
    todays_sales = Sale.objects.filter(sale_date=today).count()
    invoices_count = Sale.objects.count()
    total_stock = (
        InventoryItem.objects.aggregate(total=Sum("quantity_on_hand"))["total"] or 0
    )
    recent_sales = Sale.objects.order_by("-sale_date")[:5]

    context = {
        "profile": profile,
        "products_count": products_count,
        "low_stock_count": low_stock_count,
        "todays_sales": todays_sales,
        "invoices_count": invoices_count,
        "total_stock": total_stock,
        "recent_sales": recent_sales,
    }
    return render(request, "index.html", context)

@login_required
@role_required([StaffProfile.ROLE_ADMIN])
def admin_dashboard(request):
    # Reuse index stats but include staff stats
    staff_profiles = StaffProfile.objects.select_related("user")
    context = {
        "profile": ensure_profile(request.user),
        "staff_profiles": staff_profiles,
    }
    return render(request, "admin_dashboard.html", context)


@login_required
def productPage(request):
    products = Product.objects.all()
    product_count = Product.objects.count()
    return render(
        request, "productIndex.html", {"products": products, "product_count": product_count}
    )

@login_required
@role_required([StaffProfile.ROLE_ADMIN, StaffProfile.ROLE_STAFF])
def productCreate(request):
    if request.method == "POST":
        name = request.POST.get("name")
        category = request.POST.get("category")
        description = request.POST.get("description")
        price = request.POST.get("price")
        gst = request.POST.get("gst")
        barcode = request.POST.get("barcode") or None
        stock = request.POST.get("stock")
        image = request.FILES.get("image")

        try:
            prd = Product.objects.create(
                name=name,
                category=category,
                description=description,
                price=price or 0,
                gst=gst or 0,
                barcode=barcode,
                image=image,
            )
            prd.save()

            # Optionally create initial stock in default warehouse if provided
            if stock:
                default_warehouse, _ = Warehouse.objects.get_or_create(
                    name="Main Warehouse"
                )
                InventoryItem.objects.update_or_create(
                    product=prd,
                    warehouse=default_warehouse,
                    defaults={"quantity_on_hand": int(stock)},
                )
            messages.success(request, "Product created successfully!")
        except Exception as e:
            messages.error(request, f"Error creating product: {e}")
    return render(request, "productCreation.html")


@login_required
@role_required([StaffProfile.ROLE_ADMIN])
def productEdit(request, pk):
    product = get_object_or_404(Product, id=pk)
    if request.method == "POST":
        product.name = request.POST.get("name")
        product.category = request.POST.get("category")
        product.description = request.POST.get("description")
        product.price = request.POST.get("price") or product.price
        product.gst = request.POST.get("gst") or product.gst
        product.barcode = request.POST.get("barcode") or product.barcode
        product.active = bool(request.POST.get("active", "on"))

        if "image" in request.FILES:
            product.image = request.FILES["image"]

        product.save()
        messages.success(request, "Product updated.")
        return redirect("product page")
    return render(request, "editProduct.html", {"product": product})

@login_required
@role_required([StaffProfile.ROLE_ADMIN])
def productDelete(request, pk):
    product = get_object_or_404(Product, id=pk)
    product.active = False
    product.save()
    messages.success(request, "Product deactivated.")
    return redirect("product page")

@login_required
@role_required([StaffProfile.ROLE_ADMIN])
def uplodeCsv(request):
    if request.method == "POST" and request.FILES.get("csv_file"):
        csv_file = request.FILES["csv_file"]
        try:
            decode_file = csv_file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decode_file)

            for row in reader:
                try:
                    Product.objects.update_or_create(
                        name=row.get("name", "").strip(),
                        defaults={
                            "category": row.get("category", "").strip(),
                            "price": float(row.get("price", 0)),
                            "gst": float(row.get("gst", 0)),
                            "description": row.get("description", "").strip(),
                            "barcode": row.get("barcode", "").strip() or None,
                        },
                    )
                except Exception as e_row:
                    print(f"Skipping row due to error: {row}, Error: {e_row}")
            messages.success(request, "CSV uploaded successfully!")
        except Exception as e:
            messages.error(request, f"Failed to process CSV: {e}")
    return render(request, "csvUplode.html")

@login_required
@role_required([StaffProfile.ROLE_ADMIN])
def exportCsv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="products.csv"'
    writer = csv.writer(response)
    writer.writerow(["name", "category", "price", "description", "gst", "barcode"])
    for product in Product.objects.all():
        writer.writerow(
            [
                product.name,
                product.category,
                product.price,
                product.description,
                product.gst,
                product.barcode or "",
            ]
        )

    return response




@login_required
@role_required([StaffProfile.ROLE_ADMIN, StaffProfile.ROLE_STAFF])
def inventory(request):
    inventory_items = (
        InventoryItem.objects.select_related("product", "warehouse", "supplier").order_by(
            "product__name"
        )
    )

    stats = {
        "total_stock": inventory_items.aggregate(total=Sum("quantity_on_hand"))["total"] or 0,
        "low_stock": inventory_items.filter(
            quantity_on_hand__lte=F("low_stock_threshold")
        ).count(),
        "out_of_stock": inventory_items.filter(quantity_on_hand=0).count(),
        "total_categories": Product.objects.values("category").distinct().count(),
    }

    context = {
        "inventory_items": inventory_items,
        "products": Product.objects.order_by("name"),
        "warehouses": Warehouse.objects.order_by("name"),
        "suppliers": Supplier.objects.order_by("name"),
        "stats": stats,
    }
    return render(request, "inventory.html", context)


@login_required
@role_required([StaffProfile.ROLE_ADMIN])
def stockAdding(request):
    if request.method == "POST":
        product_id = request.POST.get("product")
        supplier_id = request.POST.get("supplier")
        warehouse_id = request.POST.get("warehouse")
        quantity = request.POST.get("quantity")
        expiry_date = request.POST.get("expiry_date")
        batch_number = request.POST.get("batch_number")
        barcode = request.POST.get("barcode")
        notes = request.POST.get("notes")

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except (TypeError, ValueError):
            messages.error(request, "Please provide a valid quantity.")
            return redirect("addStock")

        expiry_date_value = None
        if expiry_date:
            try:
                expiry_date_value = datetime.strptime(expiry_date, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid expiry date.")
                return redirect("addStock")

        try:
            product = Product.objects.get(id=product_id)
            warehouse = Warehouse.objects.get(id=warehouse_id)
            supplier = Supplier.objects.get(id=supplier_id) if supplier_id else None
        except (Product.DoesNotExist, Warehouse.DoesNotExist):
            messages.error(request, "Please select a valid product and warehouse.")
            return redirect("addStock")
        except Supplier.DoesNotExist:
            messages.error(request, "Selected supplier does not exist.")
            return redirect("addStock")

        try:
            with transaction.atomic():
                inventory_item, _ = InventoryItem.objects.select_for_update().get_or_create(
                    product=product,
                    warehouse=warehouse,
                    defaults={
                        "supplier": supplier,
                        "expiry_date": expiry_date_value,
                    },
                )
                inventory_item.quantity_on_hand += quantity
                if supplier:
                    inventory_item.supplier = supplier
                if expiry_date_value:
                    inventory_item.expiry_date = expiry_date_value
                inventory_item.save()

                StockEntry.objects.create(
                    product=product,
                    supplier=supplier,
                    warehouse=warehouse,
                    inventory_item=inventory_item,
                    quantity_added=quantity,
                    expiry_date=expiry_date_value,
                    batch_number=batch_number or "",
                    barcode=barcode,
                    notes=notes,
                )
        except Exception as exc:
            messages.error(request, f"Error adding stock: {exc}")
            return redirect("addStock")

        messages.success(request, "Stock added successfully!")
        return redirect("addStock")

    products = Product.objects.all()
    suppliers = Supplier.objects.all()
    warehouses = Warehouse.objects.all()
    context = {"suppliers": suppliers, "products": products, "warehouses": warehouses}

    return render(request, "addStock.html", context)

@login_required
@role_required([StaffProfile.ROLE_ADMIN])
def stockReducing(request):
    products = Product.objects.order_by("name")
    warehouses = Warehouse.objects.order_by("name")

    if request.method == "POST":
        product_id = request.POST.get("product")
        warehouse_id = request.POST.get("warehouse")
        quantity = request.POST.get("quantity")
        sale_price = request.POST.get("sale_price")
        customer_name = request.POST.get("customer_name", "").strip()
        sale_date = request.POST.get("sale_date")
        reason = request.POST.get("reason")
        notes = request.POST.get("notes", "").strip()

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except (TypeError, ValueError):
            messages.error(request, "Please enter a valid quantity.")
            return redirect("reduceStock")

        sale_price_value = None
        if sale_price:
            try:
                sale_price_value = Decimal(sale_price)
            except Exception:
                messages.error(request, "Invalid sale price.")
                return redirect("reduceStock")

        sale_date_value = timezone.now().date()
        if sale_date:
            try:
                sale_date_value = datetime.strptime(sale_date, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid sale date.")
                return redirect("reduceStock")

        if reason not in dict(StockReduction.REASON_CHOICES):
            messages.error(request, "Please choose a valid reason.")
            return redirect("reduceStock")

        try:
            product = Product.objects.get(id=product_id)
            warehouse = Warehouse.objects.get(id=warehouse_id)
        except (Product.DoesNotExist, Warehouse.DoesNotExist):
            messages.error(request, "Please select a valid product and warehouse.")
            return redirect("reduceStock")

        try:
            with transaction.atomic():
                inventory_item = InventoryItem.objects.select_for_update().get(
                    product=product, warehouse=warehouse
                )
                if inventory_item.quantity_on_hand < quantity:
                    messages.error(request, "Not enough stock available.")
                    return redirect("reduceStock")

                inventory_item.quantity_on_hand -= quantity
                inventory_item.save()

                StockReduction.objects.create(
                    product=product,
                    warehouse=warehouse,
                    inventory_item=inventory_item,
                    quantity_removed=quantity,
                    sale_price=sale_price_value,
                    customer_name=customer_name,
                    sale_date=sale_date_value,
                    reason=reason,
                    notes=notes,
                )
        except InventoryItem.DoesNotExist:
            messages.error(
                request, "No inventory record found for this product and warehouse."
            )
            return redirect("reduceStock")
        except Exception as exc:
            messages.error(request, f"Unable to reduce stock: {exc}")
            return redirect("reduceStock")

        messages.success(request, "Stock reduced successfully.")
        return redirect("reduceStock")

    context = {
        "products": products,
        "warehouses": warehouses,
    }
    return render(request, "reduceStock.html", context)

@login_required
@role_required([StaffProfile.ROLE_ADMIN])
def addSupplier(request):
    if request.method == "POST":
        name = request.POST.get("name")
        contact_number = request.POST.get("contact_number")
        email = request.POST.get("email")
        address = request.POST.get("address")

        try:
            supplier = Supplier.objects.create(
                name=name, contact_number=contact_number, email=email, address=address
            )
            supplier.save()
            messages.success(request, "Supplier added successfully!")
        except Exception as e:
            messages.error(request, f"Error adding supplier: {e}")
    return render(request, "addSupplier.html")


def _render_pdf_from_template(template_name, context, output_path):
    html = render_to_string(template_name, context)
    with open(output_path, "wb") as out_file:
        pisa.CreatePDF(io.BytesIO(html.encode("utf-8")), dest=out_file)
    return output_path


@login_required
@role_required([StaffProfile.ROLE_ADMIN, StaffProfile.ROLE_STAFF])
def billing(request):
    products = Product.objects.filter(active=True).order_by("name")
    warehouses = Warehouse.objects.order_by("name")
    inventory_snapshot = InventoryItem.objects.select_related("product", "warehouse")

    if request.method == "POST":
        customer_name = request.POST.get("customer_name", "").strip()
        customer_phone = request.POST.get("customer_phone", "").strip()
        customer_email = request.POST.get("customer_email", "").strip()
        staff_name = request.POST.get("staff_name", "").strip() or request.user.get_full_name()
        sale_date_value = request.POST.get("sale_date")
        notes = request.POST.get("notes", "").strip()
        product_ids = request.POST.getlist("item_product[]")
        quantity_values = request.POST.getlist("item_quantity[]")
        price_values = request.POST.getlist("item_price[]")
        warehouse_ids = request.POST.getlist("item_warehouse[]")

        if not product_ids:
            messages.error(request, "Add at least one product to generate a bill.")
            return redirect("billing")

        if not (
            len(product_ids)
            == len(quantity_values)
            == len(price_values)
            == len(warehouse_ids)
        ):
            messages.error(request, "Invalid billing data submitted.")
            return redirect("billing")

        sale_date_object = timezone.now().date()
        if sale_date_value:
            try:
                sale_date_object = datetime.strptime(sale_date_value, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid sale date.")
                return redirect("billing")

        sale_items_payload = []
        subtotal = Decimal("0.00")
        tax_amount = Decimal("0.00")

        try:
            with transaction.atomic():
                for idx, product_id in enumerate(product_ids):
                    quantity = int(quantity_values[idx] or 0)
                    if quantity <= 0:
                        raise ValueError("Quantity must be positive for all line items.")

                    product = Product.objects.get(id=product_id)
                    warehouse = Warehouse.objects.get(id=warehouse_ids[idx])
                    try:
                        inventory_item = InventoryItem.objects.select_for_update().get(
                            product=product, warehouse=warehouse
                        )
                    except InventoryItem.DoesNotExist:
                        raise ValueError(
                            f"No inventory found for {product.name} in {warehouse.name}. Please add stock first."
                        )
                    if inventory_item.quantity_on_hand < quantity:
                        raise ValueError(
                            f"Not enough stock for {product.name} in {warehouse.name}."
                        )

                    unit_price_value = price_values[idx] or None
                    unit_price = (
                        Decimal(unit_price_value) if unit_price_value else product.price
                    )
                    line_total = (unit_price * quantity).quantize(
                        TWO_PLACES, ROUND_HALF_UP
                    )
                    gst_percent = product.gst or Decimal("0")
                    gst_amount = (
                        line_total * gst_percent / Decimal("100")
                    ).quantize(TWO_PLACES, ROUND_HALF_UP)

                    subtotal += line_total
                    tax_amount += gst_amount

                    sale_items_payload.append(
                        {
                            "product": product,
                            "warehouse": warehouse,
                            "inventory_item": inventory_item,
                            "quantity": quantity,
                            "unit_price": unit_price,
                            "line_total": line_total,
                            "gst_percent": gst_percent,
                        }
                    )

                invoice_number = request.POST.get("invoice_number") or _generate_invoice_number()
                total_amount = (subtotal + tax_amount).quantize(TWO_PLACES, ROUND_HALF_UP)
                sale_record = Sale.objects.create(
                    invoice_number=invoice_number,
                    customer_name=customer_name,
                    staff_name=staff_name,
                    sale_date=sale_date_object,
                    notes=notes,
                    subtotal=subtotal,
                    tax_amount=tax_amount,
                    total_amount=total_amount,
                    created_by=request.user,
                )

                for payload in sale_items_payload:
                    SaleItem.objects.create(
                        sale=sale_record,
                        product=payload["product"],
                        warehouse=payload["warehouse"],
                        quantity=payload["quantity"],
                        unit_price=payload["unit_price"],
                        gst_percent=payload["gst_percent"],
                        line_total=payload["line_total"],
                    )

                    item = payload["inventory_item"]
                    item.quantity_on_hand -= payload["quantity"]
                    item.save()

                    StockReduction.objects.create(
                        product=payload["product"],
                        warehouse=payload["warehouse"],
                        inventory_item=item,
                        sale=sale_record,
                        quantity_removed=payload["quantity"],
                        sale_price=payload["unit_price"],
                        customer_name=customer_name,
                        sale_date=sale_date_object,
                        reason=StockReduction.SALE,
                        notes=notes,
                    )

                # Generate PDF
                invoice_dir = settings.MEDIA_ROOT / "invoices"
                invoice_dir.mkdir(parents=True, exist_ok=True)
                pdf_path = invoice_dir / f"{sale_record.invoice_number}.pdf"
                _render_pdf_from_template(
                    "invoice_print.html",
                    {"sale": sale_record, "items": sale_record.items.all()},
                    pdf_path,
                )
                sale_record.pdf_file = f"invoices/{pdf_path.name}"
                sale_record.save(update_fields=["pdf_file"])

        except Exception as exc:
            messages.error(request, f"Unable to generate bill: {exc}")
            return redirect("billing")

        messages.success(request, f"Billing complete. Invoice #{sale_record.invoice_number}.")
        return redirect("invoice_detail", pk=sale_record.pk)

    context = {
        "products": products,
        "warehouses": warehouses,
        "inventory_snapshot": inventory_snapshot,
        "inventory_data": list(
            inventory_snapshot.values("product_id", "warehouse_id", "quantity_on_hand")
        ),
        "today": timezone.now().date(),
    }
    return render(request, "billing.html", context)


@login_required
def invoice_detail(request, pk):
    sale = get_object_or_404(Sale.objects.prefetch_related("items__product", "items__warehouse"), pk=pk)
    return render(request, "invoice_detail.html", {"sale": sale, "items": sale.items.all()})


@login_required
def invoice_pdf(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if not sale.pdf_file:
        raise Http404("PDF not generated.")
    pdf_full_path = settings.MEDIA_ROOT / sale.pdf_file.name
    if not pdf_full_path.exists():
        raise Http404("PDF missing on disk.")
    return FileResponse(open(pdf_full_path, "rb"), content_type="application/pdf")


@login_required
@role_required([StaffProfile.ROLE_ADMIN])
def inventory_reports(request):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    staff_id = request.GET.get("staff")

    sales_qs = Sale.objects.all().order_by("-sale_date")
    if start_date:
        sales_qs = sales_qs.filter(sale_date__gte=start_date)
    if end_date:
        sales_qs = sales_qs.filter(sale_date__lte=end_date)
    if staff_id:
        sales_qs = sales_qs.filter(created_by_id=staff_id)

    inventory_items = InventoryItem.objects.select_related("product", "warehouse")
    recent_entries = (
        StockEntry.objects.select_related("product", "warehouse").order_by("-date_added")[:5]
    )
    recent_reductions = (
        StockReduction.objects.select_related("product", "warehouse").order_by("-created_at")[:5]
    )
    low_stock = inventory_items.filter(quantity_on_hand__lte=F("low_stock_threshold"))
    total_sales_value = sales_qs.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")

    context = {
        "inventory_items": inventory_items,
        "recent_entries": recent_entries,
        "recent_reductions": recent_reductions,
        "recent_sales": sales_qs[:20],
        "low_stock": low_stock,
        "total_stock": inventory_items.aggregate(total=Sum("quantity_on_hand"))["total"] or 0,
        "total_sales_value": total_sales_value,
        "staff_users": StaffProfile.objects.select_related("user"),
        "filters": {"start_date": start_date, "end_date": end_date, "staff_id": staff_id},
    }
    return render(request, "reports.html", context)


@login_required
@role_required([StaffProfile.ROLE_ADMIN])
def warehouse_management(request):
    warehouses = Warehouse.objects.order_by("name")
    if request.method == "POST":
        name = request.POST.get("name")
        location = request.POST.get("location", "")
        contact_person = request.POST.get("contact_person", "")
        phone = request.POST.get("phone", "")
        notes = request.POST.get("notes", "")

        if not name:
            messages.error(request, "Warehouse name is required.")
        else:
            Warehouse.objects.update_or_create(
                name=name,
                defaults={
                    "location": location,
                    "contact_person": contact_person,
                    "phone": phone,
                    "notes": notes,
                },
            )
            messages.success(request, f"Warehouse '{name}' saved successfully.")
            return redirect("warehouse_management")
    return render(request, "warehouse_manager.html", {"warehouses": warehouses})


@login_required
@role_required([StaffProfile.ROLE_ADMIN])
def edit_inventory_item(request, pk):
    inventory_item = get_object_or_404(InventoryItem, pk=pk)
    suppliers = Supplier.objects.order_by("name")

    if request.method == "POST":
        threshold = request.POST.get("low_stock_threshold")
        quantity = request.POST.get("quantity_on_hand")
        expiry_date_value = request.POST.get("expiry_date")
        supplier_id = request.POST.get("supplier")

        try:
            inventory_item.low_stock_threshold = int(threshold)
            inventory_item.quantity_on_hand = int(quantity)
            if inventory_item.quantity_on_hand < 0:
                raise ValueError("Quantity cannot be negative.")
        except (TypeError, ValueError) as exc:
            messages.error(request, f"Invalid data: {exc}")
            return redirect("editInventoryItem", pk=pk)

        if expiry_date_value:
            try:
                inventory_item.expiry_date = datetime.strptime(expiry_date_value, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid expiry date.")
                return redirect("editInventoryItem", pk=pk)
        else:
            inventory_item.expiry_date = None

        if supplier_id:
            try:
                inventory_item.supplier = Supplier.objects.get(id=supplier_id)
            except Supplier.DoesNotExist:
                messages.error(request, "Supplier not found.")
                return redirect("editInventoryItem", pk=pk)
        else:
            inventory_item.supplier = None

        inventory_item.save()
        messages.success(request, "Inventory item updated.")
        return redirect("inventory")

    context = {
        "item": inventory_item,
        "suppliers": suppliers,
    }
    return render(request, "inventory_item_form.html", context)


@login_required
@role_required([StaffProfile.ROLE_ADMIN])
def delete_inventory_item(request, pk):
    inventory_item = get_object_or_404(InventoryItem, pk=pk)
    inventory_item.delete()
    messages.success(request, "Inventory record deleted.")
    return redirect("inventory")


@login_required
def stock_level_api(request):
    product_id = request.GET.get("product")
    warehouse_id = request.GET.get("warehouse")
    current_stock = 0

    if product_id and warehouse_id:
        try:
            inventory_item = InventoryItem.objects.get(product_id=product_id, warehouse_id=warehouse_id)
            current_stock = inventory_item.quantity_on_hand
        except InventoryItem.DoesNotExist:
            current_stock = 0

    return JsonResponse({"current_stock": current_stock})


@login_required
def expiry_risk_view(request):
    stock_entries = StockEntry.objects.all()
    risk_level = None
    days_left = None
    selected_entry = None

    if request.method == "POST":
        entry_id = request.POST.get("entry_id")
        selected_entry = StockEntry.objects.get(id=entry_id)

        expiry = selected_entry.expiry_date
        risk_level, days_left = predict_expiry_risk(expiry)

    context = {
        "stock_entries": stock_entries,
        "risk_level": risk_level,
        "days_left": days_left,
        "selected": selected_entry,
    }

    return render(request, "expiry_predict.html", context)


@login_required
@role_required([StaffProfile.ROLE_ADMIN])
def staff_management(request):
    staff_profiles = StaffProfile.objects.select_related("user").order_by("user__username")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            email = request.POST.get("email")
            name = request.POST.get("name")
            role = request.POST.get("role", StaffProfile.ROLE_STAFF)
            password = request.POST.get("password") or "Staff@123"
            if not email:
                messages.error(request, "Email is required.")
                return redirect("staff_management")
            user, created = User.objects.get_or_create(
                username=email,
                defaults={"email": email, "first_name": name.split(" ")[0] if name else ""},
            )
            if created:
                user.set_password(password)
                user.save()
            profile = ensure_profile(user)
            profile.role = role
            profile.save()
            messages.success(request, "Staff saved.")
            return redirect("staff_management")
        elif action == "toggle":
            profile_id = request.POST.get("profile_id")
            profile = get_object_or_404(StaffProfile, id=profile_id)
            profile.active = not profile.active
            profile.save(update_fields=["active"])
            messages.success(request, "Status updated.")
            return redirect("staff_management")
        elif action == "reset":
            profile_id = request.POST.get("profile_id")
            profile = get_object_or_404(StaffProfile, id=profile_id)
            new_password = request.POST.get("new_password") or "Staff@123"
            profile.user.set_password(new_password)
            profile.user.save()
            messages.success(request, "Password reset.")
            return redirect("staff_management")

    return render(
        request,
        "staff_management.html",
        {"staff_profiles": staff_profiles},
    )


@login_required
@role_required([StaffProfile.ROLE_ADMIN])
def sales_page(request):
    today = timezone.now().date()
    last_30 = today - timedelta(days=30)
    sales = Sale.objects.filter(sale_date__gte=last_30)

    daily = (
        sales.values("sale_date")
        .annotate(total=Sum("total_amount"))
        .order_by("sale_date")
    )

    return render(request, "sales.html", {"sales": sales, "daily": daily})


@login_required
@role_required([StaffProfile.ROLE_ADMIN, StaffProfile.ROLE_STAFF])
def ml_page(request):
    """Comprehensive ML page with sales prediction and product demand forecasting."""
    from sklearn.linear_model import LinearRegression
    import numpy as np

    # Sales Prediction Section
    sales_message = None
    sales_prediction = None
    model_name = "sales_linear_regression"

    sales = Sale.objects.values("sale_date").annotate(total=Sum("total_amount")).order_by("sale_date")
    if sales.count() >= 2:
        days = np.array([(row["sale_date"] - sales[0]["sale_date"]).days for row in sales]).reshape(-1, 1)
        totals = np.array([float(row["total"]) for row in sales])
        reg = LinearRegression()
        reg.fit(days, totals)
        tomorrow_offset = np.array([[ (timezone.now().date() - sales[0]["sale_date"]).days + 1 ]])
        sales_prediction = reg.predict(tomorrow_offset)[0]

        # persist model artifact
        model_dir = settings.MEDIA_ROOT / "ml_models"
        model_dir.mkdir(parents=True, exist_ok=True)
        import joblib

        model_path = model_dir / f"{model_name}.pkl"
        joblib.dump(reg, model_path)
        MLModelArtifact.objects.update_or_create(
            name=model_name,
            defaults={
                "model_file": f"ml_models/{model_name}.pkl",
                "trained_on_rows": sales.count(),
                "notes": "Linear regression on daily totals",
            },
        )
    else:
        sales_message = "Not enough sales data to train. Create a few invoices first."

    # Product Demand Prediction Section
    products = Product.objects.filter(active=True).order_by("name")
    demand_predictions = []
    
    def get_sales_history_for_product(product_id):
        """Helper function to get sales history for a product."""
        # Get last 60 days of sales for this product
        start_date = timezone.now().date() - timedelta(days=60)
        sale_items = SaleItem.objects.filter(
            product_id=product_id,
            sale__sale_date__gte=start_date
        ).select_related('sale').order_by('sale__sale_date')
        
        # Group by date
        daily_sales = defaultdict(int)
        for item in sale_items:
            daily_sales[item.sale.sale_date] += item.quantity
        
        # Convert to list of dicts
        history = [
            {'date': date, 'quantity': qty}
            for date, qty in sorted(daily_sales.items())
        ]
        return history
    
    # Get demand predictions
    demand_predictions = []
    if products.exists():
        try:
            # Get current stock for each product and prepare for prediction
            products_list = list(products)
            for product in products_list:
                # Get total stock across all warehouses
                total_stock = InventoryItem.objects.filter(
                    product=product
                ).aggregate(total=Sum('quantity_on_hand'))['total'] or 0
                product.current_stock = total_stock
            
            # Get demand predictions
            sales_history_func = lambda pid: get_sales_history_for_product(pid)
            demand_predictions = predict_all_products_demand(products_list, sales_history_func, days_ahead=7)
            
            # Sort by predicted demand (highest first)
            if demand_predictions:
                demand_predictions.sort(key=lambda x: x.get('predicted_demand', 0), reverse=True)
        except Exception as e:
            # If prediction fails, return empty list
            # Log error in development (you can add proper logging if needed)
            print(f"Error in demand prediction: {e}")
            demand_predictions = []

    return render(
        request,
        "ml_page.html",
        {
            "sales_prediction": sales_prediction,
            "sales_message": sales_message,
            "sales_samples": list(sales),
            "demand_predictions": demand_predictions,
            "total_products": products.count(),
        },
    )