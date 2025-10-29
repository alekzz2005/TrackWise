from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg
from django.http import HttpResponse
from accounts.models import UserProfile, Company
from inventory.models import Product
import csv
from django.utils import timezone
from datetime import datetime, timedelta

@login_required
def reports_dashboard(request):
    """Main reports dashboard"""
    try:
        if request.user.userprofile.role != 'business_owner':
            messages.error(request, 'You do not have permission to view reports.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('dashboard')
    
    company = request.user.userprofile.company
    
    # Basic statistics for the dashboard
    total_staff = UserProfile.objects.filter(company=company, role='staff').count()
    total_products = Product.objects.filter(company=company).count()
    
    # Fix: Calculate total inventory value manually since it's a property
    products = Product.objects.filter(company=company)
    total_inventory_value = sum(product.total_value for product in products)
    
    # Low stock alert
    low_stock_products = Product.objects.filter(
        company=company, 
        quantity__gt=0, 
        quantity__lte=10
    ).count()
    
    context = {
        'company': company,
        'total_staff': total_staff,
        'total_products': total_products,
        'total_inventory_value': total_inventory_value,
        'low_stock_products': low_stock_products,
    }
    return render(request, 'reports/reports_dashboard.html', context)

@login_required
def staff_activity_report(request):
    """View activity summaries by staff"""
    try:
        if request.user.userprofile.role != 'business_owner':
            messages.error(request, 'You do not have permission to view reports.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('dashboard')
    
    company = request.user.userprofile.company
    
    # Date range filtering
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # Get staff members
    staff_members = UserProfile.objects.filter(company=company, role='staff')
    
    # Get products for activity tracking
    products = Product.objects.filter(company=company)
    
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            products = products.filter(updated_at__date__gte=start_date_obj)
        except ValueError:
            messages.error(request, 'Invalid start date format.')
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            products = products.filter(updated_at__date__lte=end_date_obj)
        except ValueError:
            messages.error(request, 'Invalid end date format.')
    
    # Prepare staff activity data
    staff_activity_data = []
    for staff in staff_members:
        # For now, we'll use simple counts. Later you can add actual activity tracking
        staff_products_count = products.count()  # This would be more specific in a real implementation
        
        activity_data = {
            'staff': staff,
            'total_products_managed': staff_products_count,
            'days_since_joined': (timezone.now().date() - staff.date_joined).days,
            'is_active': staff.is_active,
        }
        staff_activity_data.append(activity_data)
    
    # Export functionality
    export_format = request.GET.get('export')
    if export_format == 'csv':
        return export_staff_activity_csv(staff_activity_data, start_date, end_date)
    
    context = {
        'staff_activity_data': staff_activity_data,
        'start_date': start_date,
        'end_date': end_date,
        'total_staff': staff_members.count(),
    }
    return render(request, 'reports/staff_activity_report.html', context)

@login_required
def inventory_report(request):
    """Inventory summary report"""
    try:
        if request.user.userprofile.role != 'business_owner':
            messages.error(request, 'You do not have permission to view reports.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('dashboard')
    
    company = request.user.userprofile.company
    products = Product.objects.filter(company=company)
    
    # Date range filtering
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            products = products.filter(created_at__date__gte=start_date_obj)
        except ValueError:
            messages.error(request, 'Invalid start date format.')
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            products = products.filter(created_at__date__lte=end_date_obj)
        except ValueError:
            messages.error(request, 'Invalid end date format.')
    
    # Category filtering
    category_filter = request.GET.get('category', '')
    if category_filter:
        products = products.filter(category=category_filter)
    
    # Calculate report statistics
    total_products = products.count()
    total_inventory_value = sum(product.total_value for product in products)
    low_stock_count = products.filter(quantity__gt=0, quantity__lte=10).count()
    out_of_stock_count = products.filter(quantity=0).count()
    
    # Category breakdown
    category_stats = []
    for category_code, category_name in Product.CATEGORY_CHOICES:
        category_products = products.filter(category=category_code)
        if category_products.exists():
            category_stats.append({
                'code': category_code,
                'name': category_name,
                'count': category_products.count(),
                'total_value': sum(p.total_value for p in category_products),
                'percentage': (category_products.count() / total_products) * 100 if total_products > 0 else 0
            })
    
    # Export functionality
    export_format = request.GET.get('export')
    if export_format == 'csv':
        return export_inventory_csv(products, category_stats)
    
    context = {
        'products': products,
        'category_stats': category_stats,
        'total_products': total_products,
        'total_inventory_value': total_inventory_value,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'start_date': start_date,
        'end_date': end_date,
        'category_filter': category_filter,
        'categories': Product.CATEGORY_CHOICES,
    }
    return render(request, 'reports/inventory_report.html', context)

def export_staff_activity_csv(staff_activity_data, start_date, end_date):
    """Export staff activity report to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="staff_activity_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Staff Activity Report'])
    if start_date and end_date:
        writer.writerow([f'Date Range: {start_date} to {end_date}'])
    writer.writerow([])
    writer.writerow(['Staff Name', 'Department', 'Position', 'Status', 'Days Since Joined', 'Products Managed'])
    
    for activity in staff_activity_data:
        staff = activity['staff']
        writer.writerow([
            staff.user.get_full_name() or staff.user.username,
            staff.get_department_display(),
            staff.position,
            'Active' if staff.is_active else 'Inactive',
            activity['days_since_joined'],
            activity['total_products_managed']
        ])
    
    return response

def export_inventory_csv(products, category_stats):
    """Export inventory report to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="inventory_report_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Inventory Report'])
    writer.writerow([f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}'])
    writer.writerow([])
    
    # Category summary
    writer.writerow(['Category Summary'])
    writer.writerow(['Category', 'Product Count', 'Total Value', 'Percentage'])
    for stat in category_stats:
        writer.writerow([
            stat['name'],
            stat['count'],
            f"${stat['total_value']:.2f}",
            f"{stat['percentage']:.1f}%"
        ])
    
    writer.writerow([])
    writer.writerow(['Product Details'])
    writer.writerow(['Product Name', 'Category', 'Quantity', 'Unit Price', 'Total Value', 'Stock Status'])
    
    for product in products:
        if product.quantity == 0:
            stock_status = 'Out of Stock'
        elif product.quantity <= 10:
            stock_status = 'Low Stock'
        else:
            stock_status = 'In Stock'
        
        writer.writerow([
            product.item_name,
            product.get_category_display(),
            product.quantity,
            f"${product.cost_price:.2f}",
            f"${product.total_value:.2f}",
            stock_status
        ])
    
    return response