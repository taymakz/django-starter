import re

email_regex = r'^\S+@\S+\.\S+$'
phone_regex = r'^(\+98|0)?9\d{9}$'


def validate_phone(phone):
    return re.match(phone_regex, phone)


def validate_email(email):
    return re.match(email_regex, email)


def validate_password(password):
    if len(password) < 6 or len(password) > 18:
        return False, "کلمه عبور باید حداقل 6 و حداکثر 18 حرف باشد"

    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "کلمه عبور باید حداقل شامل یک حرف بزرگ باشد"

    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "کلمه عبور باید حداقل شامل یک حرف کوچک باشد"

    # Check for at least one digit
    if not re.search(r'\d', password):
        return False, "کلمه عبور باید شامل عدد باشد"

    return True, 'معتبر'
