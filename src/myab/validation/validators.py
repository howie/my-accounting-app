from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN

def validate_amount(amount: str | Decimal) -> Decimal:
    """
    Validates that the amount is a valid decimal.
    Rounds to 2 decimal places using ROUND_HALF_EVEN (Banker's rounding).
    Returns the Decimal object.
    """
    if isinstance(amount, str):
        try:
            d = Decimal(amount)
        except InvalidOperation:
             raise ValueError(f"Invalid amount format: {amount}")
    elif isinstance(amount, (int, float)):
        # Convert float/int to Decimal (convert float via string to avoid precision issues)
        d = Decimal(str(amount))
    elif isinstance(amount, Decimal):
        d = amount
    else:
        raise ValueError("Amount must be a string, number, or Decimal")
        
    # Quantize to 2 decimal places
    d = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    
    return d
