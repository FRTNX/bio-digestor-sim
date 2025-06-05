import re
import secrets

def uuid():
    """Generate unique identifier."""
    return re.sub('x', lambda m: secrets.choice('0123456789ABCDEF'), 'xxxxxxxx')
