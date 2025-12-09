from decimal import Decimal, ROUND_HALF_UP
import csv
from datetime import datetime

from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, F, Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone

from ml.expiry_predict import predict_expiry_risk
from .models import (
    InventoryItem,
    Product,
    Sale,
    SaleItem,
    StockEntry,
    StockReduction,
    Supplier,
    Warehouse,
)


def _generate_invoice_number():
    return timezone.now().strftime("INV%Y%m%d%H%M%S")


TWO_PLACES = Decimal("0.01")
# Create your views here.
def index(request):
    return render(request,'index.html')

def productPage(request):

    products=Product.objects.all()
    #print(products)
    product_count=Product.objects.count()
    return render(request,'productIndex.html',{'products':products, 'product_count': product_count})

def productCreate(request):
    if request.method =='POST':
        name=request.POST.get('name')
        category=request.POST.get('category')
        description=request.POST.get('description')
        price=request.POST.get('price')
        gst=request.POST.get('gst')
        image=request.FILES.get('image')
        #print(name,category,description,price,gst,image)
        try:
            prd=Product.objects.create(
            name=name,
            category=category,
            description=description,
            price=price,
            gst=gst,
            image=image
        )
            prd.save()
            messages.success(request, "Product created successfully!")
        except Exception as e:
            messages.error(request, f"Error creating product: {e}")
    return render(request,'productCreation.html')


def productEdit(request,pk):
    product=get_object_or_404(Product,id=pk)
    #print(product)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.category = request.POST.get('category')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.gst = request.POST.get('gst')

        if 'image' in request.FILES:
            product.image = request.FILES['image']

        product.save()
        return redirect('product page')
    return render(request,'editProduct.html',{'product': product})

def productDelete(request, pk):
    product = get_object_or_404(Product, id=pk)
    product.delete()
    return redirect('product page')

def uplodeCsv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        try:
            decode_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decode_file)
            
            for row in reader:
                try:
                    Product.objects.update_or_create(
                        name=row.get('name', '').strip(),
                        defaults={
                            'category': row.get('category', '').strip(),
                            'price': float(row.get('price', 0)),
                            'gst': float(row.get('gst', 0)),
                            'description': row.get('description', '').strip()
                        }
                    )
                except Exception as e_row:
                    print(f"Skipping row due to error: {row}, Error: {e_row}")
            messages.success(request, "CSV uploaded successfully!")
        except Exception as e:
            messages.error(request, f"Failed to process CSV: {e}")
    return render(request, 'csvUplode.html')

def exportCsv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products.csv"'
    writer = csv.writer(response)
    writer.writerow(['name', 'category', 'price', 'description', 'gst'])
    for product in Product.objects.all():
        writer.writerow([
            product.name,
            product.category,
            product.price,
            product.description,
            product.gst
        ])

    return response




#inventory management area

def inventory(request):
    inventory_items = (
        InventoryItem.objects.select_related('product', 'warehouse', 'supplier')
        .order_by('product__name')
    )

    stats = {
        'total_stock': inventory_items.aggregate(total=Sum('quantity_on_hand'))['total'] or 0,
        'low_stock': inventory_items.filter(quantity_on_hand__lte=F('low_stock_threshold')).count(),
        'out_of_stock': inventory_items.filter(quantity_on_hand=0).count(),
        'total_categories': Product.objects.values('category').distinct().count(),
    }

    context = {
        'inventory_items': inventory_items,
        'products': Product.objects.order_by('name'),
        'warehouses': Warehouse.objects.order_by('name'),
        'suppliers': Supplier.objects.order_by('name'),
        'stats': stats,
    }
    return render(request, 'inventory.html', context)


def stockAdding(request):
    if request.method == 'POST':
        product_id = request.POST.get('product')
        supplier_id = request.POST.get('supplier')
        warehouse_id = request.POST.get('warehouse')
        quantity = request.POST.get('quantity')
        expiry_date = request.POST.get('expiry_date')
        batch_number = request.POST.get('batch_number')
        barcode = request.POST.get('barcode')
        notes = request.POST.get('notes')

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except (TypeError, ValueError):
            messages.error(request, "Please provide a valid quantity.")
            return redirect('addStock')

        expiry_date_value = None
        if expiry_date:
            try:
                expiry_date_value = datetime.strptime(expiry_date, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid expiry date.")
                return redirect('addStock')

        try:
            product = Product.objects.get(id=product_id)
            warehouse = Warehouse.objects.get(id=warehouse_id)
            supplier = Supplier.objects.get(id=supplier_id) if supplier_id else None
        except (Product.DoesNotExist, Warehouse.DoesNotExist):
            messages.error(request, "Please select a valid product and warehouse.")
            return redirect('addStock')
        except Supplier.DoesNotExist:
            messages.error(request, "Selected supplier does not exist.")
            return redirect('addStock')

        try:
            with transaction.atomic():
                inventory_item, _ = InventoryItem.objects.select_for_update().get_or_create(
                    product=product,
                    warehouse=warehouse,
                    defaults={
                        'supplier': supplier,
                        'expiry_date': expiry_date_value,
                    }
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
                    notes=notes
                )
        except Exception as exc:
            messages.error(request, f"Error adding stock: {exc}")
            return redirect('addStock')

        messages.success(request, "Stock added successfully!")
        return redirect('addStock')

    products = Product.objects.all()
    suppliers = Supplier.objects.all()
    warehouses = Warehouse.objects.all()
    context = {
        'suppliers': suppliers,
        'products': products,
        'warehouses': warehouses
    }

    return render(request, 'addStock.html', context)

def stockReducing(request):
    products = Product.objects.order_by('name')
    warehouses = Warehouse.objects.order_by('name')

    if request.method == 'POST':
        product_id = request.POST.get('product')
        warehouse_id = request.POST.get('warehouse')
        quantity = request.POST.get('quantity')
        sale_price = request.POST.get('sale_price')
        customer_name = request.POST.get('customer_name', '').strip()
        sale_date = request.POST.get('sale_date')
        reason = request.POST.get('reason')
        notes = request.POST.get('notes', '').strip()

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except (TypeError, ValueError):
            messages.error(request, "Please enter a valid quantity.")
            return redirect('reduceStock')

        sale_price_value = None
        if sale_price:
            try:
                sale_price_value = Decimal(sale_price)
            except Exception:
                messages.error(request, "Invalid sale price.")
                return redirect('reduceStock')

        sale_date_value = timezone.now().date()
        if sale_date:
            try:
                sale_date_value = datetime.strptime(sale_date, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid sale date.")
                return redirect('reduceStock')

        if reason not in dict(StockReduction.REASON_CHOICES):
            messages.error(request, "Please choose a valid reason.")
            return redirect('reduceStock')

        try:
            product = Product.objects.get(id=product_id)
            warehouse = Warehouse.objects.get(id=warehouse_id)
        except (Product.DoesNotExist, Warehouse.DoesNotExist):
            messages.error(request, "Please select a valid product and warehouse.")
            return redirect('reduceStock')

        try:
            with transaction.atomic():
                inventory_item = InventoryItem.objects.select_for_update().get(
                    product=product,
                    warehouse=warehouse
                )
                if inventory_item.quantity_on_hand < quantity:
                    messages.error(request, "Not enough stock available.")
                    return redirect('reduceStock')

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
                    notes=notes
                )
        except InventoryItem.DoesNotExist:
            messages.error(request, "No inventory record found for this product and warehouse.")
            return redirect('reduceStock')
        except Exception as exc:
            messages.error(request, f"Unable to reduce stock: {exc}")
            return redirect('reduceStock')

        messages.success(request, "Stock reduced successfully.")
        return redirect('reduceStock')

    context = {
        'products': products,
        'warehouses': warehouses,
    }
    return render(request, 'reduceStock.html', context)

def addSupplier(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        contact_number = request.POST.get('contact_number')
        email = request.POST.get('email')
        address = request.POST.get('address')

        try:
            supplier = Supplier.objects.create(
                name=name,
                contact_number=contact_number,
                email=email,
                address=address
            )
            supplier.save()
            messages.success(request, "Supplier added successfully!")
        except Exception as e:
            messages.error(request, f"Error adding supplier: {e}")
    return render(request,'addSupplier.html')


def billing(request):
    products = Product.objects.order_by('name')
    warehouses = Warehouse.objects.order_by('name')
    inventory_snapshot = InventoryItem.objects.select_related('product', 'warehouse')

    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', '').strip()
        staff_name = request.POST.get('staff_name', '').strip()
        sale_date_value = request.POST.get('sale_date')
        notes = request.POST.get('notes', '').strip()
        product_ids = request.POST.getlist('item_product[]')
        quantity_values = request.POST.getlist('item_quantity[]')
        price_values = request.POST.getlist('item_price[]')
        warehouse_ids = request.POST.getlist('item_warehouse[]')

        if not product_ids:
            messages.error(request, "Add at least one product to generate a bill.")
            return redirect('billing')

        if not (len(product_ids) == len(quantity_values) == len(price_values) == len(warehouse_ids)):
            messages.error(request, "Invalid billing data submitted.")
            return redirect('billing')

        sale_date_object = timezone.now().date()
        if sale_date_value:
            try:
                sale_date_object = datetime.strptime(sale_date_value, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid sale date.")
                return redirect('billing')

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
                            product=product,
                            warehouse=warehouse
                        )
                    except InventoryItem.DoesNotExist:
                        raise ValueError(f"No inventory found for {product.name} in {warehouse.name}. Please add stock first.")
                    if inventory_item.quantity_on_hand < quantity:
                        raise ValueError(f"Not enough stock for {product.name} in {warehouse.name}.")

                    unit_price_value = price_values[idx] or None
                    unit_price = Decimal(unit_price_value) if unit_price_value else product.price
                    line_total = (unit_price * quantity).quantize(TWO_PLACES, ROUND_HALF_UP)
                    gst_percent = product.gst or Decimal("0")
                    gst_amount = (line_total * gst_percent / Decimal("100")).quantize(TWO_PLACES, ROUND_HALF_UP)

                    subtotal += line_total
                    tax_amount += gst_amount

                    sale_items_payload.append({
                        'product': product,
                        'warehouse': warehouse,
                        'inventory_item': inventory_item,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'line_total': line_total,
                        'gst_percent': gst_percent,
                    })

                invoice_number = request.POST.get('invoice_number') or _generate_invoice_number()
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
                )

                for payload in sale_items_payload:
                    SaleItem.objects.create(
                        sale=sale_record,
                        product=payload['product'],
                        warehouse=payload['warehouse'],
                        quantity=payload['quantity'],
                        unit_price=payload['unit_price'],
                        gst_percent=payload['gst_percent'],
                        line_total=payload['line_total'],
                    )

                    item = payload['inventory_item']
                    item.quantity_on_hand -= payload['quantity']
                    item.save()

                    StockReduction.objects.create(
                        product=payload['product'],
                        warehouse=payload['warehouse'],
                        inventory_item=item,
                        sale=sale_record,
                        quantity_removed=payload['quantity'],
                        sale_price=payload['unit_price'],
                        customer_name=customer_name,
                        sale_date=sale_date_object,
                        reason=StockReduction.SALE,
                        notes=notes
                    )
        except Exception as exc:
            messages.error(request, f"Unable to generate bill: {exc}")
            return redirect('billing')

        messages.success(request, f"Billing complete. Invoice #{sale_record.invoice_number}.")
        return redirect('billing')

    context = {
        'products': products,
        'warehouses': warehouses,
        'inventory_snapshot': inventory_snapshot,
        'inventory_data': list(
            inventory_snapshot.values('product_id', 'warehouse_id', 'quantity_on_hand')
        ),
        'today': timezone.now().date(),
    }
    return render(request, 'billing.html', context)


def inventory_reports(request):
    inventory_items = InventoryItem.objects.select_related('product', 'warehouse')
    recent_entries = StockEntry.objects.select_related('product', 'warehouse').order_by('-date_added')[:5]
    recent_reductions = StockReduction.objects.select_related('product', 'warehouse').order_by('-created_at')[:5]
    recent_sales = Sale.objects.order_by('-sale_date')[:5]
    low_stock = inventory_items.filter(quantity_on_hand__lte=F('low_stock_threshold'))

    total_sales_value = Sale.objects.aggregate(total=Sum('total_amount'))['total'] or Decimal("0.00")

    context = {
        'inventory_items': inventory_items,
        'recent_entries': recent_entries,
        'recent_reductions': recent_reductions,
        'recent_sales': recent_sales,
        'low_stock': low_stock,
        'total_stock': inventory_items.aggregate(total=Sum('quantity_on_hand'))['total'] or 0,
        'total_sales_value': total_sales_value,
    }
    return render(request, 'reports.html', context)


def warehouse_management(request):
    warehouses = Warehouse.objects.order_by('name')
    if request.method == 'POST':
        name = request.POST.get('name')
        location = request.POST.get('location', '')
        contact_person = request.POST.get('contact_person', '')
        phone = request.POST.get('phone', '')
        notes = request.POST.get('notes', '')

        if not name:
            messages.error(request, "Warehouse name is required.")
        else:
            Warehouse.objects.update_or_create(
                name=name,
                defaults={
                    'location': location,
                    'contact_person': contact_person,
                    'phone': phone,
                    'notes': notes,
                }
            )
            messages.success(request, f"Warehouse '{name}' saved successfully.")
            return redirect('warehouse_management')
    return render(request, 'warehouse_manager.html', {'warehouses': warehouses})


def edit_inventory_item(request, pk):
    inventory_item = get_object_or_404(InventoryItem, pk=pk)
    suppliers = Supplier.objects.order_by('name')

    if request.method == 'POST':
        threshold = request.POST.get('low_stock_threshold')
        quantity = request.POST.get('quantity_on_hand')
        expiry_date_value = request.POST.get('expiry_date')
        supplier_id = request.POST.get('supplier')

        try:
            inventory_item.low_stock_threshold = int(threshold)
            inventory_item.quantity_on_hand = int(quantity)
            if inventory_item.quantity_on_hand < 0:
                raise ValueError("Quantity cannot be negative.")
        except (TypeError, ValueError) as exc:
            messages.error(request, f"Invalid data: {exc}")
            return redirect('editInventoryItem', pk=pk)

        if expiry_date_value:
            try:
                inventory_item.expiry_date = datetime.strptime(expiry_date_value, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid expiry date.")
                return redirect('editInventoryItem', pk=pk)
        else:
            inventory_item.expiry_date = None

        if supplier_id:
            try:
                inventory_item.supplier = Supplier.objects.get(id=supplier_id)
            except Supplier.DoesNotExist:
                messages.error(request, "Supplier not found.")
                return redirect('editInventoryItem', pk=pk)
        else:
            inventory_item.supplier = None

        inventory_item.save()
        messages.success(request, "Inventory item updated.")
        return redirect('inventory')

    context = {
        'item': inventory_item,
        'suppliers': suppliers,
    }
    return render(request, 'inventory_item_form.html', context)


def delete_inventory_item(request, pk):
    inventory_item = get_object_or_404(InventoryItem, pk=pk)
    inventory_item.delete()
    messages.success(request, "Inventory record deleted.")
    return redirect('inventory')


def stock_level_api(request):
    product_id = request.GET.get('product')
    warehouse_id = request.GET.get('warehouse')
    current_stock = 0

    if product_id and warehouse_id:
        try:
            inventory_item = InventoryItem.objects.get(product_id=product_id, warehouse_id=warehouse_id)
            current_stock = inventory_item.quantity_on_hand
        except InventoryItem.DoesNotExist:
            current_stock = 0

    return JsonResponse({'current_stock': current_stock})


# area for ml

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
        "selected": selected_entry
    }

    return render(request, "expiry_predict.html", context)