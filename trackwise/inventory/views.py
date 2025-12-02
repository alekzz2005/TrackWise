from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Product
from .forms import ProductForm
from accounts.models import UserProfile
import base64

@login_required
def inventory_list(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('dashboard:dashboard')
    
    products = Product.objects.filter(company=profile.company)
    
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(item_name__icontains=search_query) |
            Q(category__icontains=search_query)
        )
    
    cost_filter = request.GET.get('cost_filter', '')
    if cost_filter == 'low':
        products = products.order_by('cost_price')
    elif cost_filter == 'high':
        products = products.order_by('-cost_price')
    
    total_inventory_value = sum(product.total_value for product in products)
    
    low_stock_count = products.filter(quantity__lte=10, quantity__gt=0).count()
    out_of_stock_count = products.filter(quantity=0).count()
    
    context = {
        'products': products,
        'search_query': search_query,
        'cost_filter': cost_filter,
        'profile': profile,
        'total_inventory_value': total_inventory_value,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
    }
    
    if profile.role == 'business_owner':
        return render(request, 'inventory/inventory_list.html', context)
    else:
        return render(request, 'inventory/inventory_list_staff.html', context)

@login_required
def product_detail(request, pk):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('dashboard:dashboard')
    
    product = get_object_or_404(Product, pk=pk, company=profile.company)
    
    if request.method == 'POST':
        if profile.role != 'business_owner':
            messages.error(request, 'Access denied. Only business owners can edit products.')
            return redirect('inventory:inventory_list')
        
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            # Get the product instance
            updated_product = form.save(commit=False)
            
            # Handle image upload if new image provided
            uploaded_image = request.FILES.get('image_upload')
            if uploaded_image:
                updated_product.set_image_from_file(uploaded_image)
            
            # Save the product
            updated_product.save()
            
            messages.success(request, f'Product "{product.item_name}" updated successfully!')
            return redirect('inventory:inventory_list')
        else:
            # Show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'profile': profile
    }
    
    if profile.role == 'business_owner':
        return render(request, 'inventory/product_detail.html', context)
    else:
        return render(request, 'inventory/product_detail_staff.html', context)

@login_required
def product_add(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            # Create product without committing to database
            product = form.save(commit=False)
            product.company = profile.company
            
            # Handle image upload from the new field
            uploaded_image = request.FILES.get('image_upload')
            if uploaded_image:
                product.set_image_from_file(uploaded_image)
            
            # Save the product
            product.save()
            
            messages.success(request, f'Product "{product.item_name}" added successfully!')
            return redirect('inventory:inventory_list')
        else:
            # Show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'profile': profile
    }
    return render(request, 'inventory/product_add.html', context)

# The rest of the views remain unchanged...
@login_required
def increase_stock(request, pk):
    if request.method == 'POST':
        try:
            profile = request.user.userprofile
            product = Product.objects.get(pk=pk, company=profile.company)
            product.quantity += 1
            product.save()
            company_products = Product.objects.filter(company=profile.company)
            total_products = company_products.count()
            total_inventory_value = float(sum(p.total_value for p in company_products))
            low_stock_count = company_products.filter(quantity__lte=10, quantity__gt=0).count()
            out_of_stock_count = company_products.filter(quantity=0).count()

            return JsonResponse({
                'success': True,
                'new_quantity': product.quantity,
                'total_value': float(product.total_value),
                'total_products': total_products,
                'total_inventory_value': total_inventory_value,
                'low_stock_count': low_stock_count,
                'out_of_stock_count': out_of_stock_count,
            })
        except (Product.DoesNotExist, UserProfile.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Product not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def decrease_stock(request, pk):
    if request.method == 'POST':
        try:
            profile = request.user.userprofile
            product = Product.objects.get(pk=pk, company=profile.company)
            if product.quantity > 0:
                product.quantity -= 1
                product.save()
            company_products = Product.objects.filter(company=profile.company)
            total_products = company_products.count()
            total_inventory_value = float(sum(p.total_value for p in company_products))
            low_stock_count = company_products.filter(quantity__lte=10, quantity__gt=0).count()
            out_of_stock_count = company_products.filter(quantity=0).count()

            return JsonResponse({
                'success': True,
                'new_quantity': product.quantity,
                'total_value': float(product.total_value),
                'total_products': total_products,
                'total_inventory_value': total_inventory_value,
                'low_stock_count': low_stock_count,
                'out_of_stock_count': out_of_stock_count,
            })
        except (Product.DoesNotExist, UserProfile.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Product not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def product_delete(request, pk):
    try:
        profile = request.user.userprofile
        product = Product.objects.get(pk=pk, company=profile.company)
        
        if profile.role != 'business_owner':
            messages.error(request, 'Access denied. Only business owners can delete products.')
            return redirect('inventory:inventory_list')
        
        if request.method == 'POST':
            product_name = product.item_name
            product.delete()
            messages.success(request, f'Product "{product_name}" deleted successfully!')
            return redirect('inventory:inventory_list')
    except (Product.DoesNotExist, UserProfile.DoesNotExist):
        messages.error(request, 'Product not found.')
        return redirect('inventory:inventory_list')
    
    context = {
        'product': product,
        'profile': profile
    }
    return render(request, 'inventory/product_delete.html', context)