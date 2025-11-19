from django.shortcuts import redirect, render, HttpResponse, get_object_or_404
from .models import Product,Supplier
from django.contrib import messages
import csv
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
    return render(request,'inventory.html')


def stockAdding(request):
    product=Product.objects.all()
    suppliers=Supplier.objects.all()
    context={
        'suppliers':suppliers,
        'products':product
    }
    #print(suppliers.values())
    #print(product)  
    
    return render(request,'addStock.html',context)

def stockReducing(request):
    return render(request,'reduceStock.html')

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