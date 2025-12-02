# reports/pdf_generator.py
from io import BytesIO
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os

def format_currency_php(amount):
    """Format amount as Philippine Peso using PHP"""
    try:
        amount = float(amount)
        return f"PHP {amount:,.2f}"
    except (ValueError, TypeError):
        return "PHP 0.00"

def create_inventory_pdf(inventory_data, company_name):
    """Generate professional inventory report PDF"""
    buffer = BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=2*cm,
        bottomMargin=1*cm
    )
    
    # Story holds the PDF content
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2c3e50'),
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=15,
        textColor=colors.HexColor('#34495e'),
        fontName='Helvetica-Bold'
    )
    
    company_style = ParagraphStyle(
        'CompanyStyle',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#7f8c8d')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=10
    )
    
    # HEADER
    story.append(Paragraph("INVENTORY REPORT", title_style))
    story.append(Paragraph(company_name, company_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", normal_style))
    story.append(Spacer(1, 20))
    
    # SUMMARY SECTION
    story.append(Paragraph("SUMMARY", subtitle_style))
    
    summary_data = [
        ["METRIC", "VALUE"],
        ["Total Items", str(inventory_data.get('total_items', 0))],
        ["Low Stock Items", str(inventory_data.get('low_stock_items', 0))],
        ["Out of Stock Items", str(inventory_data.get('out_of_stock_items', 0))],
        ["Total Inventory Value", format_currency_php(inventory_data.get('total_value', 0))]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 30))
    
    # DETAILED ITEMS SECTION
    story.append(Paragraph("INVENTORY ITEMS", subtitle_style))
    
    if inventory_data.get('items'):
        # Prepare table data
        items_data = [
            ["NO.", "ITEM NAME", "CATEGORY", "QUANTITY", "STATUS", "UNIT PRICE", "TOTAL VALUE"]
        ]
        
        for idx, item in enumerate(inventory_data['items'], 1):
            # Determine status
            quantity = item.get('current_stock', 0)
            
            if quantity == 0:
                status = "OUT OF STOCK"
            elif quantity <= 5:
                status = "LOW STOCK"
            else:
                status = "IN STOCK"
            
            items_data.append([
                str(idx),
                item.get('name', '')[:20],
                item.get('category', ''),
                f"{quantity} {item.get('unit', '')}",
                status,
                format_currency_php(item.get('price', 0)),
                format_currency_php(item.get('total_value', 0))
            ])
        
        # Create table with column widths
        col_widths = [0.5*inch, 1.5*inch, 1*inch, 0.8*inch, 0.8*inch, 1*inch, 1*inch]
        items_table = Table(items_data, colWidths=col_widths, repeatRows=1)
        
        # Apply table styling
        items_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            
            # Data rows
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            ('ALIGN', (5, 1), (-1, -1), 'RIGHT'),
            
            # Grid and borders
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            
            # Zebra striping
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        
        story.append(items_table)
        
        # Add totals row
        story.append(Spacer(1, 20))
        
        total_value = format_currency_php(inventory_data.get('total_value', 0))
        total_items = len(inventory_data['items'])
        
        totals_data = [
            ["", "", "", "", "TOTAL ITEMS:", str(total_items), ""],
            ["", "", "", "", "GRAND TOTAL:", total_value, ""]
        ]
        
        totals_table = Table(totals_data, colWidths=col_widths)
        totals_table.setStyle(TableStyle([
            ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
            ('ALIGN', (5, 0), (5, -1), 'RIGHT'),
            ('FONTNAME', (4, 0), (5, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (4, 0), (5, -1), 9),
        ]))
        
        story.append(totals_table)
    else:
        story.append(Paragraph("No inventory items found.", normal_style))
    
    # FOOTER
    story.append(Spacer(1, 40))
    footer_text = f"Report generated by TrackWise Inventory Management System • Page 1 of 1"
    story.append(Paragraph(footer_text, 
                         ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                                       alignment=TA_CENTER, textColor=colors.grey)))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF value
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf

def create_staff_activity_pdf(staff_data, company_name):
    """Generate professional staff activity report PDF"""
    buffer = BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=2*cm,
        bottomMargin=1*cm
    )
    
    # Story holds the PDF content
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2c3e50'),
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=15,
        textColor=colors.HexColor('#34495e'),
        fontName='Helvetica-Bold'
    )
    
    # HEADER
    story.append(Paragraph("STAFF ACTIVITY REPORT", title_style))
    story.append(Paragraph(company_name, 
                         ParagraphStyle('Company', parent=styles['Heading3'], fontSize=12,
                                       alignment=TA_CENTER, textColor=colors.HexColor('#7f8c8d'))))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", 
                         ParagraphStyle('Date', parent=styles['Normal'], fontSize=10,
                                       alignment=TA_CENTER)))
    story.append(Spacer(1, 20))
    
    # SUMMARY STATISTICS - REMOVED Business Owners and Regular Staff
    if staff_data.get('summary') or ('total_staff' in staff_data):
        summary = staff_data.get('summary', {})
        
        # UPDATED: Only show Total Staff, Active Staff, and Inactive Staff
        summary_data = [
            ["METRIC", "COUNT"],
            ["Total Staff", str(staff_data.get('total_staff', summary.get('total_staff', 0)))],
            ["Active Staff", str(staff_data.get('active_staff', summary.get('active_staff', 0)))],
            ["Inactive Staff", str(staff_data.get('inactive_staff', summary.get('inactive_staff', 0)))]
            # Removed: Business Owners and Regular Staff
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 30))
    
    # STAFF DETAILS TABLE - REMOVED LOCATION COLUMN
    story.append(Paragraph("STAFF MEMBERS", subtitle_style))
    
    if staff_data.get('staff_details') or staff_data.get('staff_list'):
        staff_list = staff_data.get('staff_details') or staff_data.get('staff_list', [])
        
        if staff_list:
            # Prepare table data - REMOVED LOCATION COLUMN
            staff_data_table = [
                ["NO.", "NAME", "POSITION", "DEPARTMENT", "STATUS", "JOIN DATE"]  # Removed: "LOCATION"
            ]
            
            for idx, staff in enumerate(staff_list, 1):
                name = staff.get('name', 'N/A')
                position = staff.get('position', staff.get('role', 'N/A'))
                department = staff.get('department', 'N/A')
                status = "ACTIVE" if staff.get('is_active', True) else "INACTIVE"
                join_date = staff.get('join_date', staff.get('hire_date', 'N/A'))
                
                staff_data_table.append([
                    str(idx),
                    name[:25],  # Increased width since we removed location
                    position[:20],  # Increased width
                    department[:20],  # Increased width
                    status,
                    str(join_date)[:10] if join_date else 'N/A'
                ])
            
            # Create table - ADJUSTED COLUMN WIDTHS (6 columns instead of 7)
            col_widths = [0.5*inch, 2*inch, 1.5*inch, 1.5*inch, 0.8*inch, 1*inch]  # Removed location column width
            staff_table = Table(staff_data_table, colWidths=col_widths, repeatRows=1)
            
            # Apply styling
            staff_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                
                # Data rows
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Serial number
                ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Status column (now index 4)
                ('ALIGN', (5, 1), (5, -1), 'CENTER'),  # Join date (now index 5)
                
                # Status coloring
                ('TEXTCOLOR', (4, 1), (4, -1), lambda r, c: 
                    colors.green if staff_data_table[r][c] == "ACTIVE" else colors.red),
                
                # Grid and borders
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('PADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                
                # Zebra striping
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))
            
            story.append(staff_table)
            
            # Add totals
            story.append(Spacer(1, 20))
            total_staff = len(staff_list)
            active_count = sum(1 for s in staff_list if s.get('is_active', True))
            
            totals_text = f"Total Staff: {total_staff} • Active: {active_count} • Inactive: {total_staff - active_count}"
            story.append(Paragraph(totals_text, 
                                 ParagraphStyle('Totals', parent=styles['Normal'], fontSize=9,
                                               alignment=TA_CENTER, textColor=colors.HexColor('#2c3e50'))))
        else:
            story.append(Paragraph("No staff records found.", 
                                 ParagraphStyle('NoData', parent=styles['Normal'], fontSize=10,
                                               alignment=TA_CENTER, textColor=colors.grey)))
    else:
        story.append(Paragraph("Staff data not available.", 
                             ParagraphStyle('NoData', parent=styles['Normal'], fontSize=10,
                                           alignment=TA_CENTER, textColor=colors.grey)))
    
    # FOOTER
    story.append(Spacer(1, 40))
    footer_text = f"Report generated by TrackWise Staff Management System • Page 1 of 1"
    story.append(Paragraph(footer_text, 
                         ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                                       alignment=TA_CENTER, textColor=colors.grey)))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF value
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf

def create_sales_pdf(sales_data, company_name):
    """Generate sales report PDF with PHP formatting"""
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=2*cm,
        bottomMargin=1*cm
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    story.append(Paragraph("SALES REPORT", 
                ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18,
alignment=TA_CENTER, textColor=colors.HexColor('#2c3e50'))))
    story.append(Paragraph(company_name, 
ParagraphStyle('Company', parent=styles['Normal'], fontSize=12,
                                    alignment=TA_CENTER)))
    story.append(Spacer(1, 20))
    
    # Sales summary with PHP
    if sales_data:
        summary_data = [
            ["TOTAL SALES", format_currency_php(sales_data.get('total_sales', 0))],
            ["TOTAL ORDERS", str(sales_data.get('total_orders', 0))],
            ["AVERAGE ORDER VALUE", format_currency_php(sales_data.get('average_order', 0))],
            ["TOP PRODUCT", sales_data.get('top_product', 'N/A')],
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(summary_table)
    
    story.append(Spacer(1, 40))
    footer_text = f"Report generated by TrackWise • {datetime.now().strftime('%B %d, %Y')}"
    story.append(Paragraph(footer_text,
                      ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)))
    
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf