from rest_framework import serializers

from config.apps.media.models import Media


class MediaFileNameSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="get_file_name")

    class Meta:
        model = Media
        fields = ("name",)
