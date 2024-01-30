from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from config.apps.catalog.models import Category, Brand
from config.apps.media.serializers.front import MediaFileNameSerializer


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    image = MediaFileNameSerializer()

    class Meta:
        model = Category
        fields = (
            "id",
            "image",
            "title_ir",
            "title_en",
            "slug",
            "children",
        )

    def get_children(self, obj: Category):
        child_ids_str = getattr(obj, "tn_children_pks", "")
        # Split the comma-separated string into a list of strings
        child_ids_list = child_ids_str.split(",")
        # Convert the list of strings to a list of integers
        child_ids = [int(pk) for pk in child_ids_list if pk.isdigit()]
        children_queryset = Category.objects.filter(pk__in=child_ids).only(
            "id",
            "title_ir",
            "title_en",
            "slug",
            "image__id",
            "image__file",
            "image__width",
            "image__height",
            "tn_children_pks",
        ).select_related(
            "image"
        )
        children_serializer = CategorySerializer(
            children_queryset, many=True, context=self.context
        )
        return children_serializer.data


class CategorySerializerTest(serializers.ModelSerializer):
    image = MediaFileNameSerializer()
    children = serializers.ListField()

    class Meta:
        model = Category
        fields = (
            "id",
            "image",
            "title_ir",
            "title_en",
            "slug",
            "children",
        )


CategorySerializer.get_children = extend_schema_field(
    serializers.ListField(child=CategorySerializer())
)(CategorySerializer.get_children)


class BrandSerializer(serializers.ModelSerializer):
    image = MediaFileNameSerializer()

    class Meta:
        model = Brand
        fields = (
            "id",
            "image",
            "title_ir",
            "title_en",
        )


class HeaderDataSerializer(serializers.ModelSerializer):
    brands = BrandSerializer(many=True)
    categories = CategorySerializer(many=True)

    class Meta:
        model = Category

        fields = (
            "brands",
            "categories",
        )
