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
    ('Individual Account', 'Individual Account'),
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