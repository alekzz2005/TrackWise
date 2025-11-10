# reports/utils.py
import pandas as pd
from django.http import HttpResponse
from django.template.loader import render_to_string
from io import BytesIO
import json
from datetime import datetime

def generate_excel_report(data, report_type, filename_prefix):
    """Generate Excel report from data"""
    try:
        # Create DataFrame based on report type
        if report_type == 'inventory':
            df = pd.DataFrame(data['items'])
        elif report_type == 'staff_activity':
            df = pd.DataFrame(data['staff_details'])
        else:
            df = pd.DataFrame([data])  # Fallback for single record
        
        # Create response
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Report', index=False)
        
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx"'
        return response
        
    except Exception as e:
        return HttpResponse(f"Error generating Excel report: {str(e)}", status=500)

def generate_pdf_report(data, report_type, filename_prefix):
    """Generate PDF report with improved error handling and debugging"""
    print(f"=== PDF GENERATION DEBUG ===")
    print(f"Report type: {report_type}")
    print(f"Data keys: {list(data.keys()) if data else 'No data'}")
    
    try:
        # Try to import WeasyPrint
        from weasyprint import HTML
        print("✓ WeasyPrint imported successfully")
        
        # Generate HTML content directly instead of using templates
        html_content = generate_pdf_html(data, report_type)
        print(f"✓ HTML content generated, length: {len(html_content)}")
        
        # Generate PDF
        html = HTML(string=html_content)
        print("✓ HTML object created")
        
        result = html.write_pdf()
        print("✓ PDF generated successfully")
        
        response = HttpResponse(result, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf"'
        return response
        
    except ImportError as e:
        print(f"✗ WeasyPrint import failed: {e}")
        # Fallback if WeasyPrint is not installed
        return HttpResponse(
            "PDF export requires WeasyPrint. Install with: pip install weasyprint", 
            status=500
        )
    except Exception as e:
        print(f"✗ WeasyPrint PDF generation failed: {e}")
        # Fallback: return a simple text PDF
        return generate_fallback_pdf(data, report_type, filename_prefix)

def generate_pdf_html(data, report_type):
    """Generate HTML content for PDF based on report type"""
    if report_type == 'staff_activity':
        return generate_staff_activity_pdf_html(data)
    elif report_type == 'inventory':
        return generate_inventory_pdf_html(data)
    else:
        return generate_generic_pdf_html(data)

def generate_staff_activity_pdf_html(data):
    """Generate HTML for staff activity PDF"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Staff Activity Report</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                margin: 20px; 
                font-size: 12px;
            }}
            .header {{ 
                text-align: center; 
                margin-bottom: 30px; 
                border-bottom: 2px solid #333; 
                padding-bottom: 10px; 
            }}
            .summary {{ 
                margin-bottom: 20px; 
                background: #f5f5f5; 
                padding: 15px; 
                border-radius: 5px; 
            }}
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin-top: 20px;
                font-size: 10px;
            }}
            th, td {{ 
                border: 1px solid #ddd; 
                padding: 8px; 
                text-align: left; 
                vertical-align: top;
            }}
            th {{ 
                background-color: #4a6fa5; 
                color: white; 
                font-weight: bold;
            }}
            tr:nth-child(even) {{ 
                background-color: #f2f2f2; 
            }}
            .stats {{ 
                display: flex; 
                justify-content: space-between; 
                margin-bottom: 20px; 
            }}
            .stat-card {{ 
                background: white; 
                padding: 15px; 
                border-radius: 5px; 
                border-left: 4px solid #4a6fa5; 
                flex: 1; 
                margin: 0 10px; 
                text-align: center;
            }}
            .status-active {{ color: #38a169; font-weight: bold; }}
            .status-inactive {{ color: #e53e3e; font-weight: bold; }}
            .status-leave {{ color: #ed8936; font-weight: bold; }}
            .performance-excellent {{ color: #22543d; font-weight: bold; }}
            .performance-good {{ color: #2a4365; font-weight: bold; }}
            .performance-average {{ color: #744210; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Staff Activity Report</h1>
            <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>Total Staff</h3>
                <p style="font-size: 24px; font-weight: bold; color: #4a6fa5;">{data.get('total_staff', 0)}</p>
            </div>
            <div class="stat-card">
                <h3>Active Staff</h3>
                <p style="font-size: 24px; font-weight: bold; color: #38a169;">{data.get('active_staff', 0)}</p>
            </div>
            <div class="stat-card">
                <h3>Inactive Staff</h3>
                <p style="font-size: 24px; font-weight: bold; color: #e53e3e;">{data.get('inactive_staff', 0)}</p>
            </div>
            <div class="stat-card">
                <h3>On Leave</h3>
                <p style="font-size: 24px; font-weight: bold; color: #ed8936;">{data.get('on_leave_staff', 0)}</p>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Staff Member</th>
                    <th>Employee ID</th>
                    <th>Position</th>
                    <th>Department</th>
                    <th>Status</th>
                    <th>Tenure (Days)</th>
                    <th>Performance</th>
                    <th>Task Completion</th>
                    <th>Attendance Rate</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Check if staff_details exists and is not empty
    staff_details = data.get('staff_details', [])
    
    for staff in staff_details:
        # Safely get all values with defaults
        name = staff.get('name', 'N/A')
        email = staff.get('email', '')
        employee_id = staff.get('employee_id', 'N/A')
        position = staff.get('position', 'N/A')
        department = staff.get('department', 'N/A')
        status = staff.get('status', 'unknown')
        tenure_days = staff.get('tenure_days', 0)
        performance_level = staff.get('performance_level', 'N/A')
        performance_score = staff.get('performance_score', 0)
        task_completion = staff.get('task_completion', 0)
        attendance_rate = staff.get('attendance_rate', 0)
        
        # Determine status class
        status_class = f"status-{status}" if status in ['active', 'inactive'] else "status-leave"
        
        # Determine performance class
        if performance_level.lower() == 'excellent':
            perf_class = "performance-excellent"
        elif performance_level.lower() == 'good':
            perf_class = "performance-good"
        else:
            perf_class = "performance-average"
        
        html += f"""
                <tr>
                    <td>
                        <strong>{name}</strong>
                        <br>
                        <small style="color: #666; font-size: 9px;">{email}</small>
                    </td>
                    <td><code>{employee_id}</code></td>
                    <td>{position}</td>
                    <td>{department}</td>
                    <td class="{status_class}">{status.title()}</td>
                    <td style="text-align: center;">{tenure_days}</td>
                    <td class="{perf_class}">
                        {performance_level}<br>
                        <small>({performance_score}%)</small>
                    </td>
                    <td style="text-align: center;">{task_completion}%</td>
                    <td style="text-align: center;">{attendance_rate}%</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
        
        <div style="margin-top: 30px; text-align: center; color: #666; font-size: 10px;">
            <p>Report generated by TrackWise System | Total Records: """ + str(len(staff_details)) + """</p>
        </div>
    </body>
    </html>
    """
    return html

def generate_inventory_pdf_html(data):
    """Generate HTML for inventory PDF"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Inventory Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            .summary {{ margin-bottom: 20px; background: #f5f5f5; padding: 15px; border-radius: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            th {{ background-color: #ed8936; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Inventory Report</h1>
            <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
        </div>
        
        <div class="summary">
            <h3>Summary</h3>
            <p><strong>Total Items:</strong> {data['total_items']}</p>
            <p><strong>Low Stock Items:</strong> {data['low_stock_items']}</p>
            <p><strong>Out of Stock Items:</strong> {data['out_of_stock_items']}</p>
            <p><strong>Total Inventory Value:</strong> ${data['total_value']:,.2f}</p>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Item Name</th>
                    <th>Category</th>
                    <th>Current Stock</th>
                    <th>Status</th>
                    <th>Price</th>
                    <th>Total Value</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for item in data['items']:
        html += f"""
                <tr>
                    <td>{item['name']}</td>
                    <td>{item['category']}</td>
                    <td>{item['current_stock']} {item.get('unit', '')}</td>
                    <td>{item['status']}</td>
                    <td>${item['price']:,.2f}</td>
                    <td>${item['total_value']:,.2f}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
        
        <div style="margin-top: 30px; text-align: center; color: #666;">
            <p>Report generated by TrackWise System</p>
        </div>
    </body>
    </html>
    """
    return html

def generate_generic_pdf_html(data):
    """Generate generic HTML for PDF fallback"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
        </style>
    </head>
    <body>
        <h1>Report</h1>
        <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
        <p>Data: {len(data)} records</p>
    </body>
    </html>
    """

def generate_fallback_pdf(data, report_type, filename_prefix):
    """Fallback PDF generation when WeasyPrint fails"""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from io import BytesIO
    
    try:
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add content to PDF
        p.drawString(100, 750, f"{report_type.title()} Report")
        p.drawString(100, 730, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        if report_type == 'staff_activity':
            p.drawString(100, 700, f"Total Staff: {data['total_staff']}")
            p.drawString(100, 680, f"Active Staff: {data['active_staff']}")
            y_position = 650
            for staff in data['staff_details'][:10]:  # Show first 10 staff
                p.drawString(100, y_position, f"{staff['name']} - {staff['position']}")
                y_position -= 20
                if y_position < 100:
                    p.showPage()
                    y_position = 750
        elif report_type == 'inventory':
            p.drawString(100, 700, f"Total Items: {data['total_items']}")
            p.drawString(100, 680, f"Total Value: ${data['total_value']:,.2f}")
        
        p.save()
        buffer.seek(0)
        
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf"'
        return response
        
    except Exception as e:
        # Final fallback - return error message
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)

def generate_csv_report(data, report_type, filename_prefix):
    """Generate CSV report from data"""
    try:
        if report_type == 'inventory':
            items = data['items']
        elif report_type == 'staff_activity':
            items = data['staff_details']
        else:
            items = [data]
        
        df = pd.DataFrame(items)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{datetime.now().strftime("%Y%m%d_%H%M")}.csv"'
        df.to_csv(response, index=False)
        return response
        
    except Exception as e:
        return HttpResponse(f"Error generating CSV report: {str(e)}", status=500)