"""Explicit CSV schemas and constrained Decimal parsing."""
from datetime import date
from decimal import Decimal, InvalidOperation

INVOICE_STATUSES = {'submitted', 'recorded', 'rejected', 'cancelled', 'duplicate', 'superseded'}
ACTIVE_STATUSES = {'submitted', 'recorded'}
EXCLUDED_STATUSES = ('rejected', 'cancelled', 'duplicate', 'superseded')

SCHEMAS = {
    'vendors': ['vendor_id', 'name', 'status', 'bank_token'],
    'purchase_orders': ['po_id', 'vendor_id', 'item_id', 'quantity', 'unit_price', 'currency'],
    'goods_receipts': ['grn_id', 'po_id', 'item_id', 'quantity'],
    'invoices': ['invoice_id', 'invoice_number', 'vendor_id', 'po_id', 'item_id',
                 'quantity', 'unit_price', 'declared_total', 'currency', 'bank_token', 'invoice_date'],
}
PRIMARY_KEYS = {'vendors': 'vendor_id', 'purchase_orders': 'po_id',
                'goods_receipts': 'grn_id', 'invoices': 'invoice_id'}


def number(value: str, *, quantity: bool = False) -> Decimal:
    """Reject NaN, infinities, exponent bombs, fractional units and invalid money."""
    try:
        if not isinstance(value, str) or len(value) > 24:
            raise ValueError('Numeric value must be a short decimal string')
        n = Decimal(value)
        if not n.is_finite() or n <= 0 or n > Decimal('1000000000'):
            raise ValueError('Numeric value must be positive, finite and <= 1 billion')
        if quantity and n != n.to_integral_value():
            raise ValueError('Quantity must be a whole positive number')
        if not quantity and n.as_tuple().exponent < -2:
            raise ValueError('Money supports at most two decimal places')
        return n
    except (InvalidOperation, TypeError) as exc:
        raise ValueError('Invalid decimal value') from exc


def row_errors(table: str, row: dict[str, str]) -> list[str]:
    errors = []
    for field in SCHEMAS[table]:
        value = row.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f'{field}: required')
        elif len(value) > 120 or any(ord(c) < 32 for c in value):
            errors.append(f'{field}: invalid length or control character')
    for field in ('quantity', 'unit_price', 'declared_total'):
        if field in SCHEMAS[table] and row.get(field):
            try:
                number(row[field], quantity=field == 'quantity')
            except ValueError as exc:
                errors.append(f'{field}: {exc}')
    if 'currency' in row and row['currency'] != 'INR':
        errors.append('currency: only INR is supported')
    if table == 'vendors' and row.get('status') not in ('active', 'inactive'):
        errors.append('status: expected active or inactive')
    if table == 'invoices' and row.get('invoice_date'):
        try:
            date.fromisoformat(row['invoice_date'])
        except ValueError:
            errors.append('invoice_date: expected ISO date')
    if table == 'invoices' and (not isinstance(row.get('lifecycle_status','submitted'),str) or row.get('lifecycle_status', 'submitted') not in INVOICE_STATUSES):
        errors.append('lifecycle_status: unsupported procurement lifecycle')
    return errors
