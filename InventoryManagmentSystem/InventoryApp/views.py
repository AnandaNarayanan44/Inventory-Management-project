from django.shortcuts import render,HttpResponse

# Create your views here.
def index(request):
    return render(request,'index.html')

def productPage(request):
    return render(request,'productIndex.html')

def productCreate(request):
    return render(request,'productCreation.html')