from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect

from django.contrib.auth.decorators import login_required 
from django.views.decorators.cache import cache_control

from django.http import JsonResponse
from django.contrib import messages
from .models import User, OTP
from .utils import send_otp
from userauths.decorators import role_required
from orders.models import *

import json
from django.db.models import Sum, Count
from django.utils import timezone
from django.db.models.functions import ExtractMonth, ExtractYear, TruncMonth

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None and user.is_staff:  # Ensure only staff members can log in
            login(request, user)
            return redirect('userauths:admin_dashboard')
        else:
            return render(request, 'userauths/admin_login.html', {'error': 'Invalid email or password'})
    return render(request, 'userauths/admin_login.html')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@role_required(['admin'])
def admin_logout(request):
    logout(request)
    return redirect('userauths:admin_login')


def verify_otp(request, email):
    if request.method == "POST":
        otp_code = request.POST.get('otp')
        user = User.objects.get(email=email)
        otp = OTP.objects.filter(user=user, code=otp_code, is_used=False).last()

        if otp and otp.is_valid():
            otp.is_used = True
            otp.save()

            user.is_verified = True
            user.save()

            # Add a success message
            messages.success(request, "Signup successful! You can now log in.")
            
            # Redirect to the login page
            return redirect('userauths:customer_login')  # Replace with the name of your login URL

        # Handle invalid OTP
        messages.error(request, "Invalid or expired OTP. Please try again.")
        return redirect('verify_otp', email=email)

    return render(request, 'userauths/verify_otp.html', {'email': email})

# def customer_signup(request):
#     if request.method == "POST":
#         form = CustomerSignupForm(request.POST)
#         if form.is_valid():
#             email = form.cleaned_data['email']
            
#             # Create a temporary user instance (inactive until verified)
#             user = User.objects.create(
#                 email=email,
#                 username=form.cleaned_data['username'],
#                 first_name=form.cleaned_data['first_name'],
#                 last_name=form.cleaned_data['last_name'],
#                 phone_number=form.cleaned_data['phone_number'],
#                 is_verified=False,  # Set user as unverified
#             )
#             user.set_password(form.cleaned_data['password'])
#             user.save()

#             # Send OTP after user is created
#             otp_code = send_otp(email, user)

#             # Redirect to OTP verification page
#             return redirect('userauths:verify_otp', email=email)
#     else:
#         form = CustomerSignupForm()
#     return render(request, 'userauths/customer_signup.html', {'form': form})


# def customer_login(request):
#     if request.method == "POST":
#         form = CustomerLoginForm(request.POST)
#         if form.is_valid():
#             email = form.cleaned_data['email']
#             password = form.cleaned_data['password']
#             user = authenticate(request, email=email, password=password)

#             if user:
#                 if user.is_verified:
#                     login(request, user)
#                     return redirect('homeapp:home')  # Redirect to home page
#                 else:
#                     return JsonResponse({'error': 'Please verify your email.'}, status=400)
#             return JsonResponse({'error': 'Invalid credentials.'}, status=400)
#     else:
#         form = CustomerLoginForm()
#     return render(request, 'userauths/customer_login.html', {'form': form})

from django.core.paginator import Paginator
from django.db.models import Q

@role_required(['admin'])
def user_management(request):
    search_query = request.GET.get('search', '')
    users = User.objects.all().order_by('-date_joined')

    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) | 
            Q(username__icontains=search_query)
        )

    paginator = Paginator(users, 6)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "users": page_obj,  # This is the paginated list now
        "search_query": search_query
    }
    return render(request, "userauths/user_management.html", context)



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@role_required(['admin'])
def admin_dashboard(request):

    #Gross Revenue = sum(Selling Price Per Order Item x Quantity)
    revenue = OrderMain.objects.filter(order_status='Delivered').aggregate(total=Sum('total_amount'))['total'] or 0

    #Total order count
    orders_count = OrderMain.objects.filter(order_status='Delivered').aggregate(total_orders=Count('id'))['total_orders'] or 0

    #Total discount
    total_discount = OrderMain.objects.filter(order_status='Delivered').aggregate(discount=Sum('discount_amount'))['discount'] or 0 
    
    #Monthly earnings
    now = timezone.now()
    current_year = now.year
    current_month = now.month

    monthly_earnings = OrderMain.objects.filter(
        order_status="Delivered",
        date__year = current_year,
        date__month = current_month).aggregate(monthly_total = Sum('total_amount'))['monthly_total'] or 0

    #Order Chart data
    monthly_order_count = OrderMain.objects.filter(order_status = "Delivered").annotate(
        month=ExtractMonth('date'), year = ExtractYear('date')
    ).values('year', 'month').annotate(count=Count('id')).order_by('year','month')

    chart_labels = [f'{entry["month"]}/{entry["year"]}' for entry in monthly_order_count]
    chart_data = [entry['count'] for entry in monthly_order_count]

    #User registration data
    user_registrations = User.objects.annotate(month = TruncMonth('date_joined')).values('month').annotate(count=Count('id')).order_by('month')
    user_labels = [entry['month'].strftime('%b %Y') for entry in user_registrations]
    user_data = [entry['count'] for entry in user_registrations]

    context = {
        'revenue': revenue,
        'orders_count': orders_count,
        'total_discount': total_discount,
        'monthly_earnings': monthly_earnings,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'user_labels': json.dumps(user_labels),
        'user_data': json.dumps(user_data)
    }

    return render(request, 'userauths/admin_dash.html',context) 



def best_selling_products(request):
    best_selling_products = OrderSub.objects.filter(
        main_order__order_status="Delivered"
    ).values(
        'variant__product__id',
        'variant__product__name'
    ).annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')

    top_product = best_selling_products.first()

    return render(request, 'userauths/best_product.html', {
        'top_product': top_product,
        'best_selling_products': best_selling_products
    })

def best_selling_brands(request):
    best_selling_brands = OrderSub.objects.filter(
        main_order__order_status="Delivered"
    ).values(
        'variant__product__brand__id',
        'variant__product__brand__name',
    ).annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')

    top_brand = best_selling_brands.first()

    return render(request, 'userauths/best_brands.html', {
        'top_brand': top_brand,
        'best_selling_brands': best_selling_brands
    })

def best_selling_category(request):
    best_selling_categories = OrderSub.objects.filter(
        main_order__order_status="Delivered"
    ).values(
        'variant__product__category__id',
        'variant__product__category__name',
    ).annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')
    
    top_category = best_selling_categories.first()
    
    return render(request, 'userauths/best_category.html', {
        'top_category': top_category,
        'best_selling_categories': best_selling_categories
    })


from django.utils import timezone
from datetime import timedelta


def sales_report(request):
    filter_type = request.GET.get('filter', None)

    now = timezone.now()
    start_date = end_date = None

    if filter_type == 'weekly':
        start_date = now - timedelta(days=now.weekday())
        end_date = now
    elif filter_type == 'monthly':
        start_date = now.replace(day=1)
        end_date = now

    if start_date and end_date:
        orders = OrderMain.objects.filter(
            order_status="Delivered",                    
            is_active=True,
            date__range=[start_date, end_date]
        )
    else:
        orders = OrderMain.objects.filter(
            order_status="Delivered",
            is_active=True
        )

    total_discount = orders.aggregate(total=Sum('discount_amount'))['total']
    total_orders = orders.aggregate(total=Count('id'))['total']
    total_order_amount = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    return render(request, 'userauths/sales_report.html', {
        'orders': orders,
        'total_discount': total_discount,
        'total_orders': total_orders,
        'total_order_amount': total_order_amount
    })


from datetime import datetime


def order_date_filter(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return redirect('admin_panel:sales_report')

            orders = OrderMain.objects.filter(date__range=[start_date, end_date], order_status="Delivered")

            total_discount = orders.aggregate(total=Sum('discount_amount'))['total'] or 0
            total_orders = orders.aggregate(total=Count('id'))['total'] or 0
            total_order_amount = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

            context = {
                'orders': orders,
                'total_discount': total_discount,
                'total_orders': total_orders,
                'total_order_amount': total_order_amount,
            }

            return render(request, 'userauths/sales_report.html', context)

    return redirect('userauths:sales_report')
