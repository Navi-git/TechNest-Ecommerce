from django.shortcuts import render, redirect, get_object_or_404
from category.models import Category

# Create your views here.
def index(request):
    categories = Category.objects.filter(is_active=True).order_by('name')
    return render(request, 'home/home.html', {'categories': categories})


def about(request):
    return render(request,"home/about.html")


from django.contrib import messages
from .models import Contact

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('telephone')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        if name and email and subject and message:
            Contact.objects.create(
                name=name,
                email=email,
                telephone=phone,
                subject=subject,
                message=message
            )
            messages.success(request, "Your message has been sent successfully.")
            return redirect('homeapp:contact')
        else:
            messages.error(request, "Please fill all required fields.")

    return render(request, 'home/contact.html')
