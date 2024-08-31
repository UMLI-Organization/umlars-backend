from typing import List

from rest_framework import serializers
from umlars_app.models import UmlModel, UmlFile


class UmlModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UmlModel
        fields = ["name", "description", "source_files", "formatted_data", "accessed_by", "id"]
        read_only_fields = ["tech_valid_from", "tech_valid_to", "tech_active_flag",]


class UmlFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UmlFile
        fields = ['id', 'data', 'format', 'filename', 'state']
        read_only_fields = ["tech_valid_from", "tech_valid_to", "tech_active_flag",]


class UmlModelFilesSerializer(serializers.ModelSerializer):
    source_files = UmlFileSerializer(many=True)

    class Meta:
        model = UmlModel
        fields = ["id", "source_files"]


class UmlFilesTranslationQueueMessageSerializer(serializers.ModelSerializer):
    ids_of_source_files = serializers.SerializerMethodField('_ids_of_source_files')
    ids_of_edited_files = serializers.SerializerMethodField('_ids_of_edited_files')
    ids_of_new_submitted_files = serializers.SerializerMethodField('_ids_of_new_submitted_files')
    ids_of_deleted_files = serializers.SerializerMethodField('_ids_of_deleted_files')

    def _ids_of_source_files(self, obj: UmlModel) -> List[int]:
        ids_of_source_files = self.context.get("ids_of_source_files")
        ids_of_source_files = list(ids_of_source_files) if ids_of_source_files is not None else []
        return ids_of_source_files

    def _ids_of_edited_files(self, obj: UmlModel) -> List[int]:
        ids_of_edited_files = self.context.get("ids_of_edited_files")
        ids_of_edited_files = list(ids_of_edited_files) if ids_of_edited_files is not None else []
        return ids_of_edited_files

    def _ids_of_new_submitted_files(self, obj: UmlModel) -> List[int]:
        ids_of_new_submitted_files = self.context.get("ids_of_new_submitted_files")
        ids_of_new_submitted_files = list(ids_of_new_submitted_files) if ids_of_new_submitted_files is not None else []
        return ids_of_new_submitted_files

    def _ids_of_deleted_files(self, obj: UmlModel) -> List[int]:
        ids_of_deleted_files = self.context.get("ids_of_deleted_files")
        ids_of_deleted_files = list(ids_of_deleted_files) if ids_of_deleted_files is not None else []
        return ids_of_deleted_files

    class Meta:
        model = UmlModel
        fields = ["id", "ids_of_source_files", "ids_of_edited_files", "ids_of_new_submitted_files", "ids_of_deleted_files"]


class UmlFileTranslationStatusSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    message = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = UmlFile
        fields = ['id', 'state', 'message']

    def validate(self, data):
        message = data.pop('message', None)
        if message:
            self.context['message'] = message
        return data
