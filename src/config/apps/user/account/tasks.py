from datetime import timedelta

# from celery import shared_task
from django.utils.timezone import now

from config.apps.user.account.models import User, UserVisits


# @shared_task(name="add_user_visit_celery", queue="tasks")
def add_user_visit_celery(visited_url, ip_address, user_id=None):
    try:
        if user_id:
            # Check if a visit already exists within the last 2 hours for the user
            two_hours_ago = now() - timedelta(hours=2)
            user = User.objects.get(id=user_id)
            existing_visit = UserVisits.objects.filter(user=user, url_visited=visited_url,
                                                       created_at__gte=two_hours_ago).order_by('-id').first()

            if not existing_visit:
                # Create a new visit instance
                UserVisits.objects.create(user=user, ip_address=ip_address, url_visited=visited_url)
        else:
            # Check if a visit already exists within the last 2 hours
            two_hours_ago = now() - timedelta(hours=2)
            existing_visit = UserVisits.objects.filter(ip_address=ip_address, url_visited=visited_url,
                                                       created_at__gte=two_hours_ago).order_by('-id').first()
            if not existing_visit:
                # Create a new visit instance
                UserVisits.objects.create(ip_address=ip_address, url_visited=visited_url)
    except Exception as e:
        print(f"Exception on add_user_visit_celery : {e}")
