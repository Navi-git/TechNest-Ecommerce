from django.shortcuts import render, redirect

# Create your views here.
def index(request):
    return render(request,"home/home.html")

def about(request):
    return render(request,"home/about.html")

def contact(request):
    return render(request,"home/contact.html")

def on_test(request):
    return render(request,"home/on_test.html")