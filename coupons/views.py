from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages

from django.utils import timezone
from .models import Coupon, CouponUser
from django.utils.dateparse import parse_datetime
from decimal import Decimal

from userauths.decorators import role_required
# Create your views here.from .models import Coupon, CouponUser


@role_required('admin')
def create_coupon(request):
    errors = {}
    # echo back what was submitted, even if invalid
    form_data = {
        'name':      request.POST.get('name', '').strip(),
        'code':      request.POST.get('code', '').strip(),
        'discount':  request.POST.get('discount', '').strip(),
        'minimum_purchase': request.POST.get('minimum_purchase', '').strip(),
        'maximum_discount': request.POST.get('maximum_discount', '').strip(),
        'valid_from': request.POST.get('valid_from', '').strip(),
        'valid_to':   request.POST.get('valid_to', '').strip(),
        'usage_limit': request.POST.get('usage_limit', '').strip(),
        'status':     request.POST.get('status') == 'on',
    }

    if request.method == "POST":
        # 1) Basic required-field checks
        for field in ('name','code','discount','minimum_purchase','maximum_discount','valid_from','valid_to','usage_limit'):
            if not form_data[field]:
                errors[field] = f"{field.replace('_',' ').capitalize()} is required."

        # 2) If no required-field errors, parse and type-check
        if not errors:
            # parse decimals
            for fld in ('minimum_purchase','maximum_discount','discount'):
                try:
                    form_data[fld] = Decimal(form_data[fld])
                except Exception:
                    errors[fld] = f"Invalid {fld.replace('_',' ')}."

            # parse datetimes
            vf_dt = parse_datetime(form_data['valid_from'])
            vt_dt = parse_datetime(form_data['valid_to'])
            if vf_dt is None:
                errors['valid_from'] = "Invalid valid_from format."
            else:
                form_data['valid_from'] = vf_dt
            if vt_dt is None:
                errors['valid_to'] = "Invalid valid_to format."
            else:
                form_data['valid_to'] = vt_dt

            # 3) New date‐range validations
            if vf_dt and vt_dt:
                if vf_dt.date() == vt_dt.date():
                    errors['valid_dates'] = "Valid From and Valid To dates cannot be the same."
                elif vf_dt > vt_dt:
                    errors['valid_from'] = "Valid From date cannot be after Valid To date."

            # business-rule checks
            mp = form_data.get('minimum_purchase')
            mx = form_data.get('maximum_discount')
            dc = form_data.get('discount')
            if isinstance(mp, Decimal):
                if mp < 1000 :
                    errors['minimum_purchase'] = "Minimum purchase must be greater than ₹2,000"
            if isinstance(mx, Decimal):
                if mx < 1000 or mx > 4500:
                    errors['maximum_discount'] = "Maximum discount must be between ₹1,000 and ₹4,500."
            if isinstance(dc, Decimal) and dc > 70:
                errors['discount'] = "Discount cannot exceed 70%."

        # 3) If still no errors, create and redirect
        if not errors:
            Coupon.objects.create(
                name=form_data['name'],
                code=form_data['code'],
                discount=form_data['discount'],
                minimum_purchase=form_data['minimum_purchase'],
                maximum_discount=form_data['maximum_discount'],
                valid_from=form_data['valid_from'],
                valid_to=form_data['valid_to'],
                status=form_data['status'],
                usage_limit=form_data['usage_limit'],
            )
            messages.success(request, "Coupon created successfully!")
            return redirect('coupons:coupon_list')

    # Either GET, or POST with errors → render form and let template fire SweetAlert
    return render(request, 'coupons/create_coupon.html', {
        'errors': errors,
        'form_data': form_data,
    })

@role_required('admin')
def coupon_list(request):
    coupons=Coupon.objects.all()
    return render(request, 'coupons/coupon_list.html', {'coupons':coupons})



@role_required('admin')
def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)

    # Initialize form_data from existing coupon (for GET)
    form_data = {
        'name': str(coupon.name),
        'code': str(coupon.code),
        'discount': str(coupon.discount),
        'minimum_purchase': str(coupon.minimum_purchase),
        'maximum_discount': str(coupon.maximum_discount),
        'valid_from': coupon.valid_from.strftime('%Y-%m-%dT%H:%M'),
        'valid_to':   coupon.valid_to.strftime('%Y-%m-%dT%H:%M'),
        'usage_limit': str(coupon.usage_limit),
        'status': coupon.status,
    }
    errors = {}
    if request.method == "POST":
        # 1️⃣ Pull submitted values into form_data
        for key in ('name','code','discount','minimum_purchase',
                    'maximum_discount','valid_from','valid_to','usage_limit'):
            form_data[key] = request.POST.get(key, "").strip()
        form_data['status'] = (request.POST.get('status') == 'on')

        # 2️⃣ Required‐field validation
        for fld in ('name','code','discount','minimum_purchase',
                    'maximum_discount','valid_from','valid_to','usage_limit'):
            if not form_data[fld]:
                errors[fld] = f"{fld.replace('_',' ').capitalize()} is required."

        # 3️⃣ Parse & type‐check (only if no missing‐field errors)
        if not errors:
            # ➤ Decimals
            for fld in ('minimum_purchase','maximum_discount','discount'):
                try:
                    form_data[fld] = Decimal(form_data[fld])
                except Exception:
                    errors[fld] = f"Invalid {fld.replace('_',' ')}."

            # ➤ DateTimes
            vf_dt = parse_datetime(form_data['valid_from'])
            vt_dt = parse_datetime(form_data['valid_to'])
            if vf_dt is None:
                errors['valid_from'] = "Invalid valid_from format."
            else:
                form_data['valid_from'] = vf_dt
            if vt_dt is None:
                errors['valid_to'] = "Invalid valid_to format."
            else:
                form_data['valid_to'] = vt_dt

            # ➤ New date‐range checks
            if vf_dt and vt_dt:
                if vf_dt.date() == vt_dt.date():
                    errors['valid_dates'] = "Valid From and Valid To dates cannot be the same."
                elif vf_dt > vt_dt:
                    errors['valid_from'] = "Valid From date cannot be after Valid To date."

        # 4️⃣ Business‐rule validations (only if still no errors)
        if not errors:
            mp = form_data['minimum_purchase']
            mx = form_data['maximum_discount']
            dc = form_data['discount']
            if mp < 1000 :
                errors['minimum_purchase'] = "Minimum purchase must be greater than ₹1,000 "
            if mx < 1000 or mx > 4500:
                errors['maximum_discount'] = "Maximum discount must be between ₹1,000 and ₹4,500."
            if isinstance(dc, Decimal) and dc > 70:
                errors['discount'] = "Discount cannot exceed 70%."

        # 5️⃣ If no errors, save updates and redirect
        if not errors:
            coupon.name             = form_data['name']
            coupon.code             = form_data['code']
            coupon.discount         = form_data['discount']
            coupon.minimum_purchase = form_data['minimum_purchase']
            coupon.maximum_discount = form_data['maximum_discount']
            coupon.valid_from       = form_data['valid_from']
            coupon.valid_to         = form_data['valid_to']
            coupon.status           = form_data['status']
            coupon.usage_limit      = form_data['usage_limit']
            coupon.save()

            messages.success(request, f"Coupon {coupon.name} updated successfully!")
            return redirect('coupons:coupon_list')

    # On GET or POST-with-errors → render form (template’s SweetAlert will fire if errors)
    return render(request, 'coupons/edit_coupon.html', {
        'errors': errors,
        'form_data': form_data,
        'coupon': coupon,
    })


@role_required('admin')
def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.delete()
    messages.success(request, "Coupon deleted successfully!")
    return redirect('coupons:coupon_list')


