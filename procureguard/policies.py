"""Illustrative classroom policy, not a production accounting policy."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Policy:
    price_tolerance: Decimal = Decimal('0.01')
    total_tolerance: Decimal = Decimal('0.01')
    line_exposure_tolerance: Decimal = Decimal('1.00')
    high_value: Decimal = Decimal('100000.00')
    max_rechecks: int = 1

    def __post_init__(self):
        for value in (self.price_tolerance, self.total_tolerance, self.high_value, self.line_exposure_tolerance):
            if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
                raise ValueError('Policy amounts must be finite, nonnegative Decimal values')
        if self.high_value <= 0 or type(self.max_rechecks) is not int or not 0 <= self.max_rechecks <= 1:
            raise ValueError('Positive high-value threshold and at most one recheck required')


WEIGHTS = {'PRICE_MISMATCH': 20, 'EXCESS_RECEIVED': 25, 'EXCESS_ORDERED': 25,
           'TOTAL_MISMATCH': 20, 'VENDOR_MISMATCH': 30, 'ITEM_MISMATCH': 25,
           'DUPLICATE': 40, 'BANK_CHANGE': 35, 'INACTIVE_VENDOR': 30,
           'HIGH_VALUE': 10, 'COMPOUND_RISK': 15}
WEIGHTS.update(LINE_EXPOSURE=30, CUMULATIVE_EXCESS=40, EVIDENCE_CONFLICT=40)
