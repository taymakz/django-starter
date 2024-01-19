def model_date_field_convertor(date):
    return date.strftime(
        "%a %b %d %Y %H:%M:%S GMT%z (%Z)") if date else None
