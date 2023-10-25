
TRANSACTION_TYPE_CHOICES = (
    ("DEPOSIT", 'Deposit'),
    ("WITHDRAWAL", 'Withdrawal'),
    ("TRANSFER", 'Transfer'),
    ("REFUND", 'Refund'),
    ("CREDIT", 'Credit'),
    ("EXCHANGE", 'Exchange'),
)


status = (
    ('pending', 'pending'),
    ('Awaiting Approval', 'Awaiting Approval'),
    ('Successful', 'Successful'),
    ('Received', 'Received'),
    ('failed', 'failed'),
    ('In Progress', 'In Progress'),
    ('Declined', 'Declined')
)