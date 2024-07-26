from rest_framework import serializers
from django.contrib.auth.models import User
from umlars_app.models import UmlModel, UmlModelMetadata, UmlFile


class UmlModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UmlModel
        fields = ["name", "description", "source_files", "formatted_data", "id"]
        read_only_fields = ["tech_valid_from", "tech_valid_to", "tech_active_flag",]


class UmlModelMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = UmlModelMetadata
        fields = ['data', 'model', 'id']
        read_only_fields = ["tech_valid_from", "tech_valid_to", "tech_active_flag",]


class UmlFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UmlFile
        fields = ['id', 'data', 'format', 'filename']
        read_only_fields = ["tech_valid_from", "tech_valid_to", "tech_active_flag",]


class UmlModelFilesSerializer(serializers.ModelSerializer):
    source_files = UmlFileSerializer(many=True)

    class Meta:
        model = UmlModel
        fields = ["id", "source_files"]


class UmlModelTranslationQueueMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UmlModel
        fields = ["id"]
