from enum import Enum


class VerificationMessageUsageOptions(Enum):
    AUTHENTICATE = "احراز هویت"
    RESET_PASSWORD = "بازیابی کلمه عبور"
    VERIFY = "تایید"


class VerificationMessageTypeOptions(Enum):
    PHONE = "تلفن"
    EMAIL = "ایمیل"
