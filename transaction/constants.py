
TRANSACTION_TYPE_CHOICES = (
    ("DEPOSIT", 'Deposit'),
    ("WITHDRAWAL", 'Withdrawal'),
    ("TRANSFER", 'Transfer'),
    ("REFUND", 'Refund'),
    ("CREDIT", 'Credit'),
    ("EXCHANGE", 'Exchange'),
    ("CARD FUNDING", 'CARD FUNDING'),
    ("CARD WITHDRAWAL", 'CARD WITHDRAWAL'),
    ("Card Delivery Fee", 'Card Delivery Fee'),

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