"""Constants for the admissions pipeline — no magic strings in services."""
from decimal import Decimal

# AD-12: composite score weighting (must sum to 1.0).
COMPOSITE_WEIGHTS = {
    'exam': 0.50,
    'interview_student': 0.20,
    'interview_parent': 0.15,
    'prior_academic': 0.15,
}

# AD-11: default bonus points per priority flag type.
PRIORITY_BONUSES = {
    'sibling': Decimal('2.00'),
    'staff_child': Decimal('5.00'),
    'alumni_child': Decimal('1.00'),
    'board_directive': Decimal('10.00'),
    'special_consideration': Decimal('0.00'),  # handled separately
}

# AD-41: fallback class capacity when academics.Stream is unavailable.
DEFAULT_STREAM_CAPACITY = 45

# AD-28: default offer response window.
DEFAULT_OFFER_DEADLINE_DAYS = 14

# AD-07: default enquiry follow-up reminder window.
DEFAULT_FOLLOWUP_DAYS = 3