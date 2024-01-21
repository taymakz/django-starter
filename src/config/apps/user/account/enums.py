from enum import Enum


class UserAuthenticationCheckSectionEnum(Enum):
    OTP = "ورود با کد یکبار مصرف"
    PASSWORD = "ورود با کلمه عبور"


class UsernameTypesEnum(Enum):
    PHONE = "موبایل"
    EMAIL = "ایمیل"
