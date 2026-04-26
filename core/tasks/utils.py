"""
Shared utility functions for question parsing tasks.
"""
from decimal import Decimal, ROUND_HALF_UP

# Database field constraints: max_digits=5, decimal_places=4 means range is -9.9999 to 9.9999
MAX_DECIMAL_VALUE = Decimal('9.9999')
MIN_DECIMAL_VALUE = Decimal('-9.9999')


def str_to_float(value: str, default: float = 0.0) -> float:
    """
    Parse a string value to float, returning default if parsing fails.
    
    :param value: String value to parse.
    :param default: Default value if parsing fails.
    :return: Parsed float value.
    """
    try:
        return float(value) if value and str(value).strip() else default
    except (ValueError, TypeError, AttributeError):
        return default


def clamp_decimal(value: float) -> Decimal:
    """
    Clamp a float value to fit within DecimalField(max_digits=5, decimal_places=4) constraints.
    
    :param value: Float value to clamp.
    :return: Decimal value clamped to valid range.
    """
    decimal_value = Decimal(str(value))
    if decimal_value > MAX_DECIMAL_VALUE:
        return MAX_DECIMAL_VALUE
    elif decimal_value < MIN_DECIMAL_VALUE:
        return MIN_DECIMAL_VALUE
    else:
        # Round to 4 decimal places to ensure it fits
        return decimal_value.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
