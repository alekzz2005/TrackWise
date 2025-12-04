# inventory/templatetags/number_filters.py
from django import template

register = template.Library()

@register.filter
def format_currency(value):
    """
    Format currency values with K (thousands) and M (millions) suffixes
    Example:
        ₱1,234,567.89 → ₱1.23M
        ₱12,345.67 → ₱12.35K
        ₱999.99 → ₱999.99
    """
    try:
        # Convert to float if it's not already
        num = float(value)
        
        if num == 0:
            return f"₱{num:,.2f}"
        
        abs_num = abs(num)
        suffix = ''
        
        if abs_num >= 1000000:  # Millions
            formatted = num / 1000000
            suffix = 'M'
        elif abs_num >= 1000:  # Thousands
            formatted = num / 1000
            suffix = 'K'
        else:
            # Less than 1000, show normally
            return f"₱{num:,.2f}"
        
        # Format with 2 decimal places for K/M
        if abs(formatted) >= 100:
            # For large K/M values, show 1 decimal place
            return f"₱{formatted:,.1f}{suffix}"
        else:
            # For smaller K/M values, show 2 decimal places
            return f"₱{formatted:,.2f}{suffix}"
            
    except (ValueError, TypeError):
        # If conversion fails, return original value with peso sign
        return f"₱{value}"