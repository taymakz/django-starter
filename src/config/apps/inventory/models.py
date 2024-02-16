from django.core.cache import cache
from django.db import models
from django.db.models import Q
from django.utils.timezone import now


class StockRecord(models.Model):
    product = models.OneToOneField(
        "catalog.Product", on_delete=models.CASCADE, related_name="stockrecord"
    )
    sku = models.CharField(max_length=64, null=True, blank=True, unique=True)
    buy_price = models.PositiveBigIntegerField(null=True, blank=True)
    sale_price = models.PositiveBigIntegerField()

    special_sale_price = models.PositiveBigIntegerField(null=True, blank=True)

    special_sale_price_start_at = models.DateTimeField(null=True, blank=True)
    special_sale_price_end_at = models.DateTimeField(null=True, blank=True)

    num_stock = models.IntegerField(default=0)
    in_order_limit = models.PositiveSmallIntegerField(null=True, blank=True)

    threshold_low_stack = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.sku}"

    @property
    def has_special_price_with_date(self) -> bool:
        if self.special_sale_price:
            if self.special_sale_price_end_at and not self.special_sale_price_start_at:
                return True
            elif (
                    self.special_sale_price_start_at and not self.special_sale_price_end_at
            ):
                return True
            elif self.special_sale_price_start_at and self.special_sale_price_end_at:
                return True
        return False

    @property
    def is_special_price_dates_valid(self) -> bool:
        if self.special_sale_price_start_at and not self.special_sale_price_end_at:
            return self.special_sale_price_start_at <= now()
        elif self.special_sale_price_start_at and self.special_sale_price_end_at:
            return (
                    self.special_sale_price_start_at
                    <= now()
                    <= self.special_sale_price_end_at
            )
        else:
            return False

    @property
    def final_price(self):
        if self.special_sale_price:
            if (self.special_sale_price and not (self.special_sale_price_end_at or self.special_sale_price_start_at)):
                return self.special_sale_price
            elif (
                    self.special_sale_price_start_at
                    and self.special_sale_price_end_at
                    and self.special_sale_price_start_at <= now() <= self.special_sale_price_end_at
            ):
                # Special sale price is set, and both start and end dates are provided,
                # and the current time is within the specified range.
                return self.special_sale_price
            elif (
                    self.special_sale_price_start_at
                    and not self.special_sale_price_end_at
                    and self.special_sale_price_start_at <= now()
            ):
                # Special sale price is set, start date is provided, but end date is not,
                # and the current time is after the start date.
                return self.special_sale_price
            elif (
                    not self.special_sale_price_start_at
                    and self.special_sale_price_end_at
                    and now() <= self.special_sale_price_end_at
            ):
                # Special sale price is set, end date is provided, but start date is not,
                # and the current time is before the end date.
                return self.special_sale_price

        # If no special conditions met, return the regular sale price
        return self.sale_price

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete("cached_brand_products")
        if self.product.structure == self.product.ProductTypeChoice.child:
            from config.apps.catalog.models import Product

            parent_product = (
                Product.objects.select_related("stockrecord")
                .prefetch_related("children")
                .get(id=self.product.parent.id)
            )
            childrens = parent_product.children.select_related("parent", "parent__stockrecord").filter(Q(
                Q(parent__stockrecord__num_stock__gt=0, parent__product_class__track_stock=True) |
                Q(parent__product_class__track_stock=False)
            ), is_public=True).select_related(
                "stockrecord"
            )

            if childrens.exists():
                # Initialize with the first child product's special price start and end dates
                min_start_date = None
                max_end_date = None
                minimum_stock = childrens[0].stockrecord

                # Find the minimum special price start date and the maximum special price end date and Minimum Stock
                for item in childrens:
                    if item.stockrecord.sale_price < minimum_stock.sale_price:
                        minimum_stock = item.stockrecord
                    if (
                            item.stockrecord.is_special_price_dates_valid
                            and item.stockrecord.has_special_price_with_date
                    ):
                        if (
                                item.stockrecord.special_sale_price_start_at
                                and item.stockrecord.special_sale_price_end_at
                        ):
                            if (
                                    min_start_date is None
                                    or item.stockrecord.special_sale_price_start_at
                                    < min_start_date
                            ):
                                min_start_date = (
                                    item.stockrecord.special_sale_price_start_at
                                )
                            if (
                                    max_end_date is None
                                    or item.stockrecord.special_sale_price_end_at
                                    > max_end_date
                            ):
                                max_end_date = (
                                    item.stockrecord.special_sale_price_end_at
                                )

                StockRecord.objects.update_or_create(
                    product=self.product.parent,
                    defaults={
                        "sale_price": minimum_stock.sale_price,
                        "special_sale_price": minimum_stock.special_sale_price,
                        "special_sale_price_start_at": min_start_date,
                        "special_sale_price_end_at": max_end_date,
                        "num_stock": minimum_stock.num_stock,
                    },
                )
            else:
                # If there are no child products, reset the values for the parent product to None
                StockRecord.objects.update_or_create(
                    product=self.product.parent,
                    defaults={
                        "sale_price": self.sale_price,
                        "special_sale_price": None,
                        "special_sale_price_start_at": None,
                        "special_sale_price_end_at": None,
                        "num_stock": self.num_stock,
                    },
                )
