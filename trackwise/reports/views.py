from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
import json
from .forms import ReportFilterForm, ExportFormatForm
from .models import ReportConfiguration, GeneratedReport
from .utils import generate_pdf_report, generate_excel_report, generate_csv_report
from inventory.models import Product

@login_required
def reports_dashboard(request):
    """Main reports dashboard"""
    context = {
        'active_reports': ReportConfiguration.objects.filter(is_active=True),
        'recent_reports': GeneratedReport.objects.filter(generated_by=request.user)[:5]
    }
    return render(request, 'reports/reports_dashboard.html', context)


@login_required
def staff_activity_report(request):
    """Staff Activity Report with Export Functionality - SECURED BY COMPANY"""
    try:
        from staff_management.models import StaffProfile
        from accounts.models import UserProfile
        from django.db.models import Count, Q
        import random
        
        print("=== STAFF ACTIVITY DEBUG ===")
        
        # Get the current user's profile and company
        try:
            current_user_profile = UserProfile.objects.get(user=request.user)
            user_company = current_user_profile.company
            print(f"Current user company: {user_company.name}")
        except UserProfile.DoesNotExist:
            messages.error(request, 'Your user profile is not properly configured.')
            return render(request, 'reports/staff_activity.html', {
                'error': 'User profile not configured',
                'activity_data': None
            })
        
        # ONLY fetch staff from the current user's company
        staff_profiles = StaffProfile.objects.select_related(
            'user_profile', 
            'user_profile__user',
            'user_profile__company'  # Add company to select_related
        ).filter(
            user_profile__company=user_company  # CRITICAL SECURITY FILTER
        ).all()
        
        print(f"Found {staff_profiles.count()} staff profiles in company: {user_company.name}")
        
        # Calculate basic statistics
        total_staff = staff_profiles.count()
        active_staff = staff_profiles.filter(status='active').count()
        inactive_staff = staff_profiles.filter(status='inactive').count()
        on_leave_staff = staff_profiles.filter(status='on_leave').count()
        
        # Prepare staff details for template
        staff_details = []
        for staff in staff_profiles:
            # Get basic info
            full_name = f"{staff.user_profile.user.first_name} {staff.user_profile.user.last_name}"
            
            # Calculate tenure in days
            from django.utils import timezone
            tenure_days = (timezone.now().date() - staff.hire_date).days
            
            # Generate performance metrics (simulated for demo)
            performance_score = random.randint(70, 100)
            task_completion = random.randint(75, 100)
            attendance_rate = random.randint(85, 100)
            
            # Determine performance level
            if performance_score >= 90:
                performance_level = "Excellent"
                performance_class = "success"
            elif performance_score >= 80:
                performance_level = "Good" 
                performance_class = "info"
            else:
                performance_level = "Average"
                performance_class = "warning"
            
            staff_details.append({
                'id': staff.id,
                'name': full_name,
                'employee_id': staff.employee_id,
                'position': staff.position,
                'department': staff.department,
                'status': staff.status,
                'hire_date': staff.hire_date,
                'tenure_days': tenure_days,
                'email': staff.user_profile.user.email,
                'performance_score': performance_score,
                'performance_level': performance_level,
                'performance_class': performance_class,
                'task_completion': task_completion,
                'attendance_rate': attendance_rate,
            })
        
        activity_data = {
            'total_staff': total_staff,
            'active_staff': active_staff,
            'inactive_staff': inactive_staff,
            'on_leave_staff': on_leave_staff,
            'staff_details': staff_details,
            'company_name': user_company.name,  # Add company name for context
        }
        
        # Handle export requests - SECURE EXPORTS TOO
        export_format = request.GET.get('export')
        if export_format:
            # Ensure exports also respect company filtering
            if export_format == 'excel':
                return generate_excel_report(activity_data, 'staff_activity', f'staff_activity_report_{user_company.name}')
            elif export_format == 'pdf':
                return generate_pdf_report(activity_data, 'staff_activity', f'staff_activity_report_{user_company.name}')
            elif export_format == 'csv':
                return generate_csv_report(activity_data, 'staff_activity', f'staff_activity_report_{user_company.name}')
        
        context = {
            'activity_data': activity_data,
            'debug_total_staff': total_staff,
            'company_name': user_company.name,
        }
        
        print(f"Sending {total_staff} staff members to template from company: {user_company.name}")
        return render(request, 'reports/staff_activity.html', context)
        
    except Exception as e:
        import traceback
        print(f"ERROR in staff_activity_report: {str(e)}")
        print(traceback.format_exc())
        
        return render(request, 'reports/staff_activity.html', {
            'error': f"Error loading staff data: {str(e)}",
            'activity_data': None
        })

@login_required
def inventory_report(request):
    """Inventory Report with Export Functionality - SECURED BY COMPANY"""
    try:
        from inventory.models import Product
        from accounts.models import UserProfile
        from django.db.models import Sum, Count
        
        # Get the current user's company
        try:
            current_user_profile = UserProfile.objects.get(user=request.user)
            user_company = current_user_profile.company
        except UserProfile.DoesNotExist:
            messages.error(request, 'Your user profile is not properly configured.')
            return render(request, 'reports/inventory_report.html', {
                'error': 'User profile not configured',
                'inventory_data': None
            })
        
        # ONLY fetch products from the current user's company
        products = Product.objects.filter(company=user_company).order_by('item_name')
        
        # Calculate statistics
        total_products = products.count()
        total_quantity = products.aggregate(total=Sum('quantity'))['total'] or 0
        
        # Calculate total value safely
        total_value = 0
        for product in products:
            if hasattr(product, 'total_value') and product.total_value:
                total_value += float(product.total_value)
        
        # Stock status counts
        low_stock_threshold = 10
        low_stock_items = products.filter(quantity__lte=low_stock_threshold, quantity__gt=0).count()
        out_of_stock_items = products.filter(quantity=0).count()
        
        # Prepare individual items data
        items_list = []
        for product in products:
            # Determine stock status
            if product.quantity == 0:
                status = 'Out of Stock'
            elif product.quantity <= low_stock_threshold:
                status = 'Low Stock'
            else:
                status = 'In Stock'
            
            # Calculate item value safely
            item_value = 0
            if hasattr(product, 'total_value') and product.total_value:
                item_value = float(product.total_value)
            else:
                item_value = float(product.quantity * product.cost_price)
            
            items_list.append({
                'id': product.id,
                'name': product.item_name,
                'category': product.get_category_display(),
                'current_stock': product.quantity,
                'min_stock': low_stock_threshold,
                'status': status,
                'price': float(product.cost_price),
                'unit': product.get_unit_of_measure_display(),
                'total_value': round(item_value, 2)
            })
        
        inventory_data = {
            'total_items': total_products,
            'low_stock_items': low_stock_items,
            'out_of_stock_items': out_of_stock_items,
            'total_value': round(total_value, 2),
            'items': items_list,
            'company_name': user_company.name,
        }
        
        # Handle export requests - SECURE EXPORTS TOO
        export_format = request.GET.get('export')
        if export_format:
            if export_format == 'excel':
                return generate_excel_report(inventory_data, 'inventory', f'inventory_report_{user_company.name}')
            elif export_format == 'pdf':
                return generate_pdf_report(inventory_data, 'inventory', f'inventory_report_{user_company.name}')
            elif export_format == 'csv':
                return generate_csv_report(inventory_data, 'inventory', f'inventory_report_{user_company.name}')
        
        context = {
            'inventory_data': inventory_data,
            'total_products': total_products,
            'total_quantity': total_quantity,
            'total_value': round(total_value, 2),
            'company_name': user_company.name,
        }
        
        return render(request, 'reports/inventory_report.html', context)
    
    except Exception as e:
        import traceback
        print(f"Error in inventory_report: {str(e)}")
        print(traceback.format_exc())
        
        context = {
            'inventory_data': None,
            'error': f"Error loading inventory data: {str(e)}"
        }
        return render(request, 'reports/inventory_report.html', context)


def get_staff_activity_data(start_date, end_date):
    """Get staff activity data - NOW IMPLEMENTED"""
    try:
        from staff_management.models import StaffProfile
        from django.db.models import Count, Q
        
        # Get staff data within date range (using hire_date as reference)
        staff_profiles = StaffProfile.objects.filter(
            hire_date__lte=end_date
        ).select_related('user_profile', 'user_profile__user')
        
        # Calculate basic metrics
        total_staff = staff_profiles.count()
        active_staff = staff_profiles.filter(status='active').count()
        
        # Department distribution
        department_stats = staff_profiles.values('department').annotate(
            count=Count('id')
        )
        
        return {
            'total_staff': total_staff,
            'active_staff': active_staff,
            'department_stats': list(department_stats),
            'period': f"{start_date} to {end_date}",
            'data_available': True
        }
    
    except Exception as e:
        return {
            'error': str(e),
            'data_available': False
        }

def get_inventory_data():
    """Get inventory data for export functionality"""
    from inventory.models import Product
    from django.db.models import Sum
    
    try:
        products = Product.objects.all()
        total_products = products.count()
        total_quantity = products.aggregate(total=Sum('quantity'))['total'] or 0
        
        return {
            'total_products': total_products,
            'total_quantity': total_quantity,
            'products_count': products.count()
        }
    except Exception as e:
        return {'error': str(e)}