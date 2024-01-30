from django.db import models
from django.utils.timezone import now


class StockRecord(models.Model):
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, related_name='stockrecords')
    sku = models.CharField(max_length=64, null=True, blank=True, unique=True)
    as_placeholder = models.BooleanField(default=False)
    buy_price = models.PositiveBigIntegerField(null=True, blank=True)
    sale_price = models.PositiveBigIntegerField()

    special_sale_price = models.PositiveBigIntegerField(null=True, blank=True)

    special_sale_price_start_at = models.DateTimeField(null=True, blank=True)
    special_sale_price_end_at = models.DateTimeField(null=True, blank=True)

    num_stock = models.PositiveIntegerField(default=0)
    threshold_low_stack = models.PositiveIntegerField(null=True, blank=True)

    @property
    def get_price(self):
        if (self.special_sale_price and self.special_sale_price_start_at and self.special_sale_price_end_at) and (
                self.special_sale_price_start_at <= now() <= self.special_sale_price_end_at):
            return self.special_sale_price
        else:
            return self.sale_price

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)
