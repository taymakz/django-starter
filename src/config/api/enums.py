from enum import Enum


class ResponseMessage(Enum):
    # Result Messages
    TIME_OUT = "خطای اتصال"
    SUCCESS = "عملیات با موفقیت انجام شد"
    FAILED = "خطایی در انجام عملیات رخ داده است"
    ACCESS_DENIED = "شما اجازه دسترسی ندارید"
    # Validation Messages
    NOT_VALID_EMAIL_OR_PHONE = "شماره موبایل و یا ایمیل وارد شده نامعتبر میباشد"
    NOT_VALID_EMAIL = "ایمیل وارد شده نامعتبر میباشد"
    NOT_VALID_PHONE = "شماره موبایل شده نامعتبر میباشد"

    SUBMIT_PHONE = "شماره موبایل ثبت نشده"

    # Notification Messages

    PHONE_OTP_SENT = "کد تایید به شماره {username} پیامک شد"
    EMAIL_OTP_SENT = "کد تایید به ایمیل {username} ارسال شد"
    EMAIL_NEWSLETTER_ACTIVATION_LINK_SENT = "لینک فعال سازی به ایمیل مورد نظر ارسال شد"
    EMAIL_NEWSLETTER_ACTIVATION_SUCCESS = "ایمیل شما با موفقیت تایید شد"
    EMAIL_NEWSLETTER_ACTIVATION_FAILED = "لینک فعال سازی نامعتبر و یا منقضی شده است"
    EMAIL_NEWSLETTER_EXIST = "ایمیل وارد شده قبلا ثبت شده است"
    EMAIL_NEWSLETTER_ACTIVATION_LINK_ALREADY_SENT = (
        "لینک فعال سازی به ایمیل مورد نظر قبلا ارسال شده است"
    )

    # Authentication
    AUTH_WRONG_PASSWORD = "کلمه عبور اشتباه میباشد"
    AUTH_WRONG_OTP = "کد تایید اشتباه میباشد"
    AUTH_LOGIN_SUCCESSFULLY = "با موفقیت وارد شدید"
    AUTH_LOGOUT_SUCCESSFULLY = "با موفقیت خارج شدید"

    # Reset Password
    RESET_PASSWORD_USER_NOT_FOUND = "کاربری با مشخصات وارد شده یافت نشد"
    RESET_PASSWORD_SUCCESSFULLY = "کلمه عبور جدید با موفقیت ثبت شد"
    PASSWORD_CONFIRM_MISMATCH = "کلمه های عبور یکسان نمیباشند"

    # Orders
    ORDER_ADDED_TO_CART_SUCCESSFULLY = "محصول به سبد خرید اضافه شد"
    ORDER_ITEM_DOES_NOT_EXIST_MORE_THAN = "بیشتر از {stock} عدد موجود نمی باشد"
    ORDER_ITEM_REACH_MAXIMUM_IN_ORDER_LIMIT = (
        "حداکثر {stock} عدد از این محصول میتواند در سبد خرید باشد"
    )
    ORDER_ITEM_COUNT_INCREASED = "به تعداد محصول در سبد خرید اضافه شد"
    ORDER_ITEM_COUNT_DECREASED = "از تعداد محصول در سبد خرید کم شد"
    ORDER_ITEM_REMOVED = "محصول از سبد خرید حذف شد"
    ORDER_ITEM_CLEARED = "تمامی محصولات سبد خرید حذف شد"
    # Favorite
    PRODUCT_ADDED_TO_FAVORITE_SUCCESSFULLY = "محصول به علاقه مندی‌ها اضافه شد"
    PRODUCT_REMOVED_FROM_FAVORITE_SUCCESSFULLY = "محصول از علاقه مندی‌ها حذف شد"
    PRODUCTS_CLEAR_FROM_FAVORITE_SUCCESSFULLY = "تمامی محصولات لیست علاقه مندی‌ حذف شد"

    PRODUCTS_CLEAR_FROM_RECENT_SUCCESSFULLY = (
        "تمامی محصولات لیست بازدید های اخیر‌ حذف شد"
    )

    # User Panel Address
    USER_PANEL_ADDRESS_TO_MUCH = "امکان ساخت بیش از 5 آدرس وجود ندارد"
    USER_PANEL_ADDRESS_ADDED_SUCCESSFULLY = "آدرس جدید با موفقیت ثبت شد"
    USER_PANEL_ADDRESS_REMOVED_SUCCESSFULLY = "آدرس مورد نظر حذف شد"
    USER_PANEL_ADDRESS_EDITED_SUCCESSFULLY = "آدرس با موفقیت ویرایش شد"
    USER_PANEL_ADDRESS_NOT_FOUND = "آدرسی یافت نشد"
    USER_PANEL_PHONE_ALREADY_EXIST = "شماره موبایل وارد شده قبلا ثبت شده است"
    USER_PANEL_EMAIL_ALREADY_EXIST = "ایمیل وارد شده قبلا ثبت شده است"
    USER_PANEL_CURRENT_PASSWORD_WRONG = "کلمه عبور فعلی اشتباه میباشد"

    # Coupon
    COUPON_NOT_VALID = "کد تخفیف وارد شده نا معتبر می باشد"
    # Payment
    PAYMENT_NOT_VALID_SELECTED_ADDRESS = "آدرس انتخاب شده نامعتبر می باشد"
    PAYMENT_NOT_VALID_SELECTED_SHIPPING = "شیوه ارسال انتخاب شده نامعتبر می باشد"
    PAYMENT_NOT_VALID_SELECTED_SHIPPING_OR_ADDRESS = (
        "شیوه ارسال و یا آدرس انتخاب شده نامعتبر می باشد"
    )
    PAYMENT_NOT_VALID_USED_COUPON = "کد تخفیف استفاده شده نامعتبر می باشد"
    PAYMENT_EMPTY_ORDER = "سبد خرید شما خالی می باشد"
