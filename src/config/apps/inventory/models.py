from django.db import models
from django.utils.timezone import now


class StockRecord(models.Model):
    product = models.OneToOneField('catalog.Product', on_delete=models.CASCADE, related_name='stockrecord')
    sku = models.CharField(max_length=64, null=True, blank=True, unique=True)
    buy_price = models.PositiveBigIntegerField(null=True, blank=True)
    sale_price = models.PositiveBigIntegerField()

    special_sale_price = models.PositiveBigIntegerField(null=True, blank=True)

    special_sale_price_start_at = models.DateTimeField(null=True, blank=True)
    special_sale_price_end_at = models.DateTimeField(null=True, blank=True)

    num_stock = models.PositiveIntegerField(default=0)
    threshold_low_stack = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.sku}"

    @property
    def get_price(self):
        if (self.special_sale_price and self.special_sale_price_start_at and self.special_sale_price_end_at) and (
                self.special_sale_price_start_at <= now() <= self.special_sale_price_end_at):
            return self.special_sale_price
        else:
            return self.sale_price

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.product.structure == self.product.ProductTypeChoice.child:
            from config.apps.catalog.models import Product
            parent_product = Product.objects.get(id=self.product.parent.id)
            childrens = parent_product.children.filter(is_public=True)
            minimum_stock: StockRecord = childrens[0].stockrecord

            for item in childrens:
                if item.stockrecord.sale_price < minimum_stock.sale_price:
                    minimum_stock = item.stockrecord

            StockRecord.objects.update_or_create(
                product=self.product.parent,
                defaults={
                    'sale_price': minimum_stock.sale_price,
                    'special_sale_price': minimum_stock.special_sale_price,
                    'special_sale_price_start_at': minimum_stock.special_sale_price_start_at,
                    'special_sale_price_end_at': minimum_stock.special_sale_price_end_at,
                    'num_stock': minimum_stock.num_stock,
                }
            )
