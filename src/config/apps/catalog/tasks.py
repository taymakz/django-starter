from datetime import timedelta

from celery import shared_task
from django.utils.timezone import now

from config.apps.catalog.models import Product, ProductVisits
from config.apps.user.account.models import User


@shared_task(name="add_product_visit", queue="tasks")
def add_product_visit_celery(product_slug, ip_address, user_id=None):
    try:
        if user_id:
            product = Product.objects.get(short_slug=product_slug)
            user = User.objects.get(id=user_id)
            # Check if a visit already exists within the last 2 hours for the user
            two_hours_ago = now() - timedelta(hours=2)
            existing_visit = ProductVisits.objects.filter(user=user, product=product,
                                                          created_at__gte=two_hours_ago).order_by('-id').first()
            if not existing_visit:
                # Create a new visit instance
                ProductVisits.objects.create(user=user, ip_address=ip_address, product=product)
        else:
            product = Product.objects.get(short_slug=product_slug)
            # Check if a visit already exists within the last 2 hours for the user
            two_hours_ago = now() - timedelta(hours=2)
            existing_visit = ProductVisits.objects.filter(product=product,
                                                          created_at__gte=two_hours_ago).order_by('-id').first()
            if not existing_visit:
                # Create a new visit instance
                ProductVisits.objects.create(ip_address=ip_address, product=product)
    except Exception as e:
        print(f"Exception on add_product_visit_celery : {e}")
