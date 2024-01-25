from django.core.management.base import BaseCommand
from rest_framework.generics import get_object_or_404

from config.apps.catalog.models import Category


class Command(BaseCommand):
    help = "Remove all expired VerifyOTPService objects"

    def handle(self, *args, **options):
        all_men_shoes: Category = Category.objects.get(pk=1)
        i = "s"
        for item in all_men_shoes.get_children():
            i += 's'
            item: Category = item
            parent_node = get_object_or_404(Category, pk=2)
            instance = parent_node.add_child(title_ir=item.title_ir, title_en=item.title_en, slug=i,
                                             image=item.image)
