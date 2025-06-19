from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.text import slugify
from .models import Category
from django.core.exceptions import ValidationError
from .validators import validate_image_size, validate_no_leading_trailing_spaces, validate_category_name, validate_image_format
from userauths.decorators import role_required


from django.core.paginator import Paginator
from django.db.models import Q

@role_required(['admin'])
def list_categories(request):
    query = request.GET.get('q')
    categories = Category.objects.all().order_by('-updated_at')

    if query:
        categories = categories.filter(Q(name__icontains=query) | Q(description__icontains=query))

    paginator = Paginator(categories, 5) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'categories': page_obj,
        'query': query,
    }
    return render(request, 'category/category_list.html', context)


@role_required(['admin'])
def add_category(request):
    if request.method == "POST":
        name = request.POST.get("name", "")
        description = request.POST.get("description", "")
        slug = request.POST.get("slug", "")
        image = request.FILES.get("image")
        parent_id = request.POST.get('parent')

        errors = []

        # Name Validations
        if not name:
            errors.append("Category name is required.")
        elif len(name) > 100:
            errors.append("Category name should not exceed 100 characters.")
        else:
            try:
                validate_no_leading_trailing_spaces(name)  # Prevents leading/trailing spaces
                validate_category_name(name)  # Ensures only letters, numbers, and spaces
                
            except ValidationError as e:
                errors.extend(e.messages)

        # Check if category name already exists
        if Category.objects.filter(name__iexact=name).exists():
            errors.append("Category name already exists.")

        # Description Validation
        if description:
            try:
                validate_no_leading_trailing_spaces(description)
            except ValidationError as e:
                errors.extend(e.messages)
        
        description = description.strip()

        if not description:
            errors.append("Description is required")
        elif description and len(description) < 10:
            errors.append("Description must be at least 10 characters long.")

        if Category.objects.filter(slug__iexact=slug).exists():
            errors.append("Slug name already exists.")

        # Image Validation
        if image:
            try:
                validate_image_size(image)
                validate_image_format(image)
            except ValidationError as e:
                errors.append(e.message)

        # Display Errors
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, "category/add_category.html", {'categories': Category.objects.filter(parent=None)})

        parent = Category.objects.get(id=parent_id) if parent_id else None

        # Save Category
        Category.objects.create(
            name=name,
            slug=slug,
            description=description,
            parent=parent,
            image=image
        )
        messages.success(request, "Category added successfully!")
        return redirect('category:admin_category_list')

    categories = Category.objects.filter(parent=None)  # Fetch main categories
    return render(request, 'category/add_category.html', {'categories': categories})

@role_required(['admin'])
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "")
        slug = request.POST.get("slug", "")
        image = request.FILES.get("image")
        parent_id = request.POST.get("parent")
        delete_image = request.POST.get("delete_image")  # Check for delete image

        errors = []

        # Name validation
        if not name:
            errors.append("Category name is required.")
        elif len(name) > 100:
            errors.append("Category name should not exceed 100 characters.")
        else:
            try:
                validate_no_leading_trailing_spaces(name)
                validate_category_name(name)
            except ValidationError as e:
                errors.extend(e.messages)

        # Unique category name validation (excluding current category)
        if Category.objects.filter(name__iexact=name).exclude(id=category.id).exists():
            errors.append("Category name already exists.")

        # Validate description for leading/trailing spaces before stripping
        if description:
            try:
                validate_no_leading_trailing_spaces(description)
            except ValidationError as e:
                errors.extend(e.messages)

        # Strip spaces after validation
        description = description.strip()

        # Description validation
        if not description:
            errors.append("Description is required")
        elif len(description) < 10:
            errors.append("Description must be at least 10 characters long.")

        if Category.objects.filter(slug__iexact=slug).exclude(id=category.id).exists():
            errors.append("Slug name already exists.")

        # Image validation
        if delete_image and not image:
            errors.append("You must upload a new image if deleting the current one.")
        elif not image and not category.image and not delete_image:
            errors.append("Exactly one image is required for the category.")
        elif image:
            try:
                validate_image_size(image)
                validate_image_format(image)
                # Check for multiple files (for robustness)
                if len(request.FILES.getlist('image')) > 1:
                    errors.append("Only one image can be uploaded.")
            except ValidationError as e:
                errors.append(e.message)

        # Display errors in the template
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, "category/edit_category.html", {
                "category": category,
                "categories": Category.objects.filter(parent=None).exclude(id=category.id)
            })

        # Update category
        category.name = name
        category.description = description
        category.slug = slug
        if image:
            category.image = image  # Update image if a new one is uploaded
        elif delete_image and image:
            category.image = image  # Replace image if delete is checked and new image is provided
        category.parent = Category.objects.get(id=parent_id) if parent_id else None

        category.save()

        messages.success(request, "Category updated successfully!")
        return redirect("category:admin_category_list")

    categories = Category.objects.filter(parent=None).exclude(id=category.id)
    return render(request, "category/edit_category.html", {
        "category": category,
        "categories": categories
    })

@role_required(['admin'])
def toggle_category_status(request, category_id):
    from .models import Category
    category = Category.objects.get(id=category_id)
    category.is_active = not category.is_active
    category.save()
    return redirect('category:admin_category_list')


@role_required(['admin'])
def delete_category(request, category_id):
    from .models import Category
    # Fetch the category or return 404 if not found
    category = get_object_or_404(Category, id=category_id)
    
    # Delete the category
    category.delete()

    # Redirect back to the admin categories page
    return redirect('category:admin_category_list')

#----------------------------------------------------------------------
#   CATEGORY OFFER ADMIN SIDE
#----------------------------------------------------------------------

# offers/views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import CategoryOffer, Category
from django.contrib import messages
from django.utils import timezone

@role_required(['admin'])
def list_category_offers(request):
    offers = CategoryOffer.objects.all()
    return render(request, 'category/offer_list.html', {'offers': offers})

@role_required(['admin'])
def add_category_offer(request):
    categories = Category.objects.exclude(offer__isnull=False)
    if request.method == "POST":
        category_id = request.POST.get('category')
        discount = request.POST.get('discount')
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')

        if not all([category_id, discount, start, end]):
            messages.error(request, "All fields are required.")
            return redirect('category:add_category_offer')

        CategoryOffer.objects.create(
            category_id=category_id,
            discount_percentage=discount,
            start_date=start,
            end_date=end
        )
        messages.success(request, "Category offer added successfully.")
        return redirect('category:list_category_offers')

    return render(request, 'category/offer_add.html', {'categories': categories})

@role_required(['admin'])
def edit_category_offer(request, offer_id):
    offer = get_object_or_404(CategoryOffer, id=offer_id)
    if request.method == "POST":
        offer.discount_percentage = request.POST.get('discount')
        offer.start_date = request.POST.get('start_date')
        offer.end_date = request.POST.get('end_date')
        offer.save()
        messages.success(request, "Offer updated successfully.")
        return redirect('category:list_category_offers')
    return render(request, 'category/offer_edit.html', {'offer': offer})

@role_required(['admin'])
def delete_category_offer(request, offer_id):
    offer = get_object_or_404(CategoryOffer, id=offer_id)
    offer.delete()
    messages.success(request, "Offer deleted.")
    return redirect('category:list_category_offers')
