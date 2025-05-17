# Create your views here.
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from userauths.decorators import role_required 

from userauths.models import User
from orders.models import OrderMain, OrderSub
from django.contrib.auth import authenticate, login


from django.contrib import messages
from .models import UserAddress
from payments.models import *

@login_required
@role_required(['customer']) 
def user_dashboard(request):
    user = request.user
    user_data = User.objects.get(email=user.email)
    user_address = UserAddress.objects.filter(user=user, is_deleted=False).order_by('-updated_at')
    orders = OrderMain.objects.filter(user=user.id).order_by('-updated_at')
    order_sub = OrderSub.objects.filter(user=user.id)
    
    # Retrieve the wallet and its transactions.
    try:
        wallet = Wallet.objects.get(user=user)
        wallet_transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')
    except Wallet.DoesNotExist:
        wallet = None
        wallet_transactions = None
    
    
    return render(request, 'user_panel/user_dash.html', {
        'user_address': user_address,
        'user_data': user_data,
        'user': user,
        'orders': orders,
        'order_sub': order_sub,
        'wallet': wallet,
        'wallet_transactions': wallet_transactions,
    })

@login_required
@role_required(['customer'])  # Adjust parameters as necessary
def user_details(request):
    # Fetch the current user using their email address.
    user_details = get_object_or_404(User, email=request.user.email)
    
    # Optionally, you could set default values if fields are blank.
    if not user_details.first_name:
        user_details.first_name = "First Name Not Provided"
    if not user_details.last_name:
        user_details.last_name = "Last Name Not Provided"
    if not getattr(user_details, 'phone_number', None):
        setattr(user_details, 'phone_number', "Phone Number Not Provided")
    
    return render(request, 'user_panel/user_details.html', {'user_details': user_details})


from django.contrib.auth import get_user_model
User = get_user_model()

@login_required
@role_required(['customer'])  # Adjust parameters as needed to enforce your role permissions
def edit_details(request, pk):
    user_obj = get_object_or_404(User, id=pk)
    
    if request.method == "GET":
        return render(request, 'user_panel/user_dash.html', {'user': user_obj})
    
    elif request.method == "POST":
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        
        if not first_name or not last_name:
            messages.error(request, "First name and last name cannot be empty.")
            return render(request, 'user_panel/user_dash.html', {'user': user_obj})
        
        if len(phone_number) != 10 or not phone_number.isdigit():
            messages.error(request, "Phone number must be 10 digits and contain only numbers.")
            return render(request, 'user_panel/user_dash.html', {'user': user_obj})
        
        user_obj.first_name = first_name
        user_obj.last_name = last_name
        user_obj.phone_number = phone_number
        user_obj.save()
        
        messages.success(request, 'Details Edited Successfully')
        return redirect('user_panel:user_dash')


# userauths/views.py

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .forms import ProfilePictureForm
import os

@login_required
@require_POST
def change_profile_picture(request):
    form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)
    if form.is_valid():
        user = request.user

        # Remove old image if it exists
        if user.profile_picture and os.path.isfile(user.profile_picture.path):
            os.remove(user.profile_picture.path)

        form.save()
        return JsonResponse({
            'status': 'success',
            'message': 'Profile picture updated successfully.',
            'profile_picture_url': user.profile_picture.url
        })
    return JsonResponse({
        'status': 'error',
        'message': 'Failed to update profile picture.',
        'errors': form.errors
    }, status=400)



@login_required
@require_POST
def remove_profile_picture(request):
    user = request.user
    if user.profile_picture:
        if os.path.isfile(user.profile_picture.path):
            os.remove(user.profile_picture.path)
        user.profile_picture.delete(save=True)

    return JsonResponse({'status': 'success', 'message': 'Profile picture removed.'})



@login_required
def change_password(request):
    if request.method == "GET":
        # Render the change password template (or a section within user_dash.html)
        return render(request, 'user_panel/user_dash.html')
    
    elif request.method == "POST":
        user = request.user

        # Retrieve the form data from the POST request.
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_new_password = request.POST.get('confirm_new_password')

        # Check if the old password provided is correct.
        if user.check_password(old_password):
            # Check if the new passwords match and are different from the old password.
            if new_password == confirm_new_password and new_password != old_password:
                # Set and save the new password.
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password Changed Successfully')
                
                # Reauthenticate the user with the new password.
                user = authenticate(username=user.email, password=new_password)
                if user is not None:
                    login(request, user)
                else:
                    messages.error(request, 'Authentication failed. Please login again.')
                
                # Redirect back to the change password page (or another appropriate page).
                return redirect('user_panel:change_password')
            else:
                messages.error(request, 'New Passwords Do Not Match or Same as Old')
        else:
            messages.error(request, 'Old Password Incorrect')

        # If errors occur, re-render the same page with error messages.
        return render(request, 'user_panel/user_dash.html')



@login_required
@role_required(['customer'])  # Remove or adjust if not needed.
def create_address(request):
    if request.method == "POST":
        user = request.user
        name = request.POST.get('name', '').strip()
        house_name = request.POST.get('house_name', '').strip()
        street_name = request.POST.get('street_name', '').strip()
        pin_number = request.POST.get('pin_number', '').strip()
        district = request.POST.get('district', '').strip()
        state = request.POST.get('state', '').strip()
        country = request.POST.get('country', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        status = request.POST.get('status') == "on"

        # Check if all required fields are provided
        if not all([name, house_name, street_name, pin_number, district, state, country, phone_number]):
            messages.error(request, "All fields are required.")
            return redirect('user_panel:user_dash')
        
        # Validate pin number: must be a 6-digit number
        if not pin_number.isdigit() or len(pin_number) != 6:
            messages.error(request, "Please enter a valid 6-digit PIN number.")
            return redirect('user_panel:user_dash')
        
        # Validate phone number: must be 10 or 12 digits
        if not phone_number.isdigit() or len(phone_number) not in [10, 12]:
            messages.error(request, "Please enter a valid phone number with 10 or 12 digits.")
            return redirect('user_panel:user_dash')
        
        # Create and save the address
        address = UserAddress.objects.create(
            user=user,
            name=name,
            house_name=house_name,
            street_name=street_name,
            pin_number=pin_number,
            district=district,
            state=state,
            country=country,
            phone_number=phone_number,
            status=status,
        )
        address.save()
        messages.success(request, 'Address Created Successfully')
        return redirect('user_panel:user_dash')
    else:
        # For non-POST requests, redirect to the dashboard.
        return redirect('user_panel:user_dash')


@login_required
@role_required(['customer']) 
def edit_address(request, pk):
    address = get_object_or_404(UserAddress, id=pk)
    
    if request.method == "GET":
        return render(request, 'user_panel/edit_address.html', {'users': address})
    
    elif request.method == "POST":
        # Assign current user to the address
        address.user = request.user
        
        # Retrieve and strip POST data
        name = request.POST.get('name', '').strip()
        house_name = request.POST.get('house_name', '').strip()
        street_name = request.POST.get('street_name', '').strip()
        pin_number = request.POST.get('pin_number', '').strip()
        district = request.POST.get('district', '').strip()
        state = request.POST.get('state', '').strip()
        country = request.POST.get('country', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        status = request.POST.get('status') == "on"
        
        # Validate required fields
        if not all([name, house_name, street_name, pin_number, district, state, country, phone_number]):
            messages.error(request, "All fields are required.")
            return redirect('user_panel:user_dash')
        
        # Validate PIN number: 6 digits and numeric
        if not pin_number.isdigit() or len(pin_number) != 6:
            messages.error(request, "Please enter a valid 6-digit PIN number.")
            return redirect('user_panel:user_dash')
        
        # Validate phone number: 10 or 12 digits and numeric
        if not phone_number.isdigit() or len(phone_number) not in [10, 12]:
            messages.error(request, "Please enter a valid phone number with 10 or 12 digits.")
            return redirect('user_panel:user_dash')
        
        # Update address fields
        address.name = name
        address.house_name = house_name
        address.street_name = street_name
        address.pin_number = pin_number
        address.district = district
        address.state = state
        address.country = country
        address.phone_number = phone_number
        
        # Handle status update:
        # If address.status was True, reset all addresses' status for this user to False.
        if address.status:
            UserAddress.objects.filter(user=address.user).update(status=False)
        address.status = status
        
        address.save()
        return redirect('user_panel:user_dash')


@login_required
@role_required(['customer'])  # Adjust or remove based on your project needs.
def add_address(request):
    if request.method == "GET":
        return render(request, 'user_panel/add_new_address.html')
    
    elif request.method == "POST":
        user = request.user
        name = request.POST.get('name', '').strip()
        house_name = request.POST.get('house_name', '').strip()
        street_name = request.POST.get('street_name', '').strip()
        pin_number = request.POST.get('pin_number', '').strip()
        district = request.POST.get('district', '').strip()
        state = request.POST.get('state', '').strip()
        country = request.POST.get('country', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        status = request.POST.get('status') == "on"

        # Validate required fields
        if not all([name, house_name, street_name, pin_number, district, state, country, phone_number]):
            messages.error(request, "All fields are required.")
            return redirect('cart:checkout')
        
        # Validate PIN number: 6-digit numeric value.
        if not pin_number.isdigit() or len(pin_number) != 6:
            messages.error(request, "Please enter a valid 6-digit PIN number.")
            return redirect('cart:checkout')
        
        # Validate phone number: numeric and either 10 or 12 digits.
        if not phone_number.isdigit() or len(phone_number) not in [10, 12]:
            messages.error(request, "Please enter a valid phone number with 10 or 12 digits.")
            return redirect('cart:checkout')
        
        # Create and save the address.
        address = UserAddress.objects.create(
            user=user,
            name=name,
            house_name=house_name,
            street_name=street_name,
            pin_number=pin_number,
            district=district,
            state=state,
            country=country,
            phone_number=phone_number,
            status=status,
        )
        address.save()
        messages.success(request, 'Address Added Successfully')
        return redirect('cart:checkout')


from django.utils import timezone

@login_required
@role_required(['customer'])  # Remove or adjust as needed.
def make_as_default(request, pk):
    user = request.user
    address = get_object_or_404(UserAddress, id=pk, user=user)
    
    # Reset all addresses to not default for this user
    UserAddress.objects.filter(user=user).update(status=False)
    
    # Set the chosen address as default and update the timestamp.
    address.status = True
    address.updated_at = timezone.now()
    address.save()
    
    messages.success(request, 'Default Address set successfully')
    return redirect('user_panel:user_dash')


@login_required
@role_required(['customer'])  # Adjust or remove based on your project needs.
def address_delete(request, pk):
    if request.method == "POST":
        address = get_object_or_404(UserAddress, id=pk)
        address.is_deleted = True
        address.save()
        messages.success(request, 'Address Deleted Successfully')
    return redirect('user_panel:user_dash')



@login_required
@role_required(['customer'])  # Remove or adjust as needed.
def toggle_address_status(request):
    if request.method == 'POST':
        try:
            address_id = request.POST.get('address_id')
            address = get_object_or_404(UserAddress, id=address_id, user=request.user, is_deleted=False)
            
            # Reset order_status for all addresses for this user.
            UserAddress.objects.filter(user=request.user).update(order_status=False)
            
            # Set order_status for the selected address.
            address.order_status = True
            address.save()
            
            return JsonResponse({'success': True})
        except UserAddress.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Address not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})



from orders.models import OrderMain, OrderSub

@login_required
@role_required(['customer'])  # Remove or adjust based on your project needs
def user_invoice(request, pk):
    order_main = OrderMain.objects.get(id=pk)
    order_sub = OrderSub.objects.filter(main_order=order_main, is_active=True)
    return render(request, 'user_panel/user_invoice.html', {
        'order_main': order_main, 
        'order_sub': order_sub
    })
