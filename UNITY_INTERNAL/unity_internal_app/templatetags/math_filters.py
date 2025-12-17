from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def sub(value, arg):
    """Subtracts the argument from the value."""
    try:
        return Decimal(value) - Decimal(arg)
    except (ValueError, TypeError):
        return 0