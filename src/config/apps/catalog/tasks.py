from celery import shared_task


@shared_task(name="add_product_visit")
def add_product_visit_celery(to, code, type, queue='celery:3'):
    pass
