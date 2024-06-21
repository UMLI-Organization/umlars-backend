from rest_framework import serializers

from umli_app.models import UmlModel, UmlModelMetadata


class UmlModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UmlModel
        fields = ["name", "description", "source_file", "formatted_data", "id"]
        read_only_fields = ["tech_valid_from", "tech_valid_to", "tech_active_flag",]


class UmlModelMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = UmlModelMetadata
        fields = ['data', 'model', 'id']
        read_only_fields = ["tech_valid_from", "tech_valid_to", "tech_active_flag",]