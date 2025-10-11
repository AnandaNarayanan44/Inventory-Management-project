from django.shortcuts import render,HttpResponse
from .models import Product
from django.contrib import messages
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

