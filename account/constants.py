MALE = 'M'
FEMALE = 'F'

GENDER_CHOICE = (
    (MALE, "Male"),
    (FEMALE, "Female"),
)
ID = (
    ('Driver License', 'Driver License'),
    ("National ID", 'National ID'),
    ('Passport', 'Passport'),
)
account_type = (
    ("Savings Account", 'Savings Account'),
    ("Checking Account", 'Checking Account'),
    ("Joint-checking Account", 'Joint-checking Account'),
    ("Business Account", 'Business Account'),

)
verification_status = (
    ('Unverified', 'Unverified'),
    ('Under Review', 'Under Review'),
    ('Verified', 'Verified')
)

status = (
    ('pending', 'pending'),
    ('Awaiting Approval', 'Awaiting Approval'),
    ('Successful', 'Successful'),
    ('Received', 'Received'),
    ('failed', 'failed'),
    ('In Progress', 'In Progress'),
    ('Expired', 'Expired')
)

investment_status = (
    ('Active', 'Active'),
    ('Expired', 'Expired'),
    ('On Hold', 'On Hold'),
)

payout_frequency = (
    ('Weekly', 'Weekly'),
    ('Twice a month (1st and 15th)', 'Twice a month (1st and 15th)'),
    ('Monthly (1st business day)', 'Monthly(1st business day)'),
    ('At the end of investment period', 'At the end of investment period'),
)