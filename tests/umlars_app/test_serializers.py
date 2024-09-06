from django.test import TestCase
from rest_framework.exceptions import ValidationError
from umlars_app.rest.serializers import (
    UmlModelSerializer, UmlFileSerializer, UmlModelFilesSerializer,
    UmlFilesTranslationQueueMessageSerializer, UmlFileTranslationStatusSerializer
)
from umlars_app.models import UmlModel, UmlFile
from django.contrib.auth.models import User


class UmlModelSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser')
        self.uml_model = UmlModel.objects.create(
            name="Test UML Model",
            description="A description",
            formatted_data="<xml>Some UML data</xml>"
        )

    def test_uml_model_serializer_valid(self):
        serializer = UmlModelSerializer(instance=self.uml_model)
        data = serializer.data
        self.assertEqual(data["name"], "Test UML Model")
        self.assertEqual(data["description"], "A description")
        

class UmlFileSerializerTests(TestCase):
    def setUp(self):
        self.uml_model = UmlModel.objects.create(
            name="Test UML Model",
            description="A description"
        )
        self.uml_file = UmlFile.objects.create(
            data="<xml>Some UML data</xml>",
            filename="diagram.xmi",
            format=UmlFile.SupportedFormat.EA_XMI,
            state=10,
            model=self.uml_model
        )

    def test_uml_file_serializer_valid(self):
        serializer = UmlFileSerializer(instance=self.uml_file)
        data = serializer.data
        self.assertEqual(data["filename"], "diagram.xmi")
        self.assertEqual(data["format"], UmlFile.SupportedFormat.EA_XMI)

    def test_uml_file_serializer_create(self):
        data = {
            "data": "<xml>New UML data</xml>",
            "filename": "new_diagram.xmi",
            "format": UmlFile.SupportedFormat.EA_XMI,
            "state": 10
        }
        serializer = UmlFileSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        new_file = serializer.save(model=self.uml_model)
        self.assertEqual(new_file.filename, "new_diagram.xmi")


class UmlModelFilesSerializerTests(TestCase):
    def setUp(self):
        self.uml_model = UmlModel.objects.create(
            name="Test UML Model",
            description="A description"
        )
        self.uml_file = UmlFile.objects.create(
            data="<xml>Some UML data</xml>",
            filename="diagram.xmi",
            format=UmlFile.SupportedFormat.EA_XMI,
            state=10,
            model=self.uml_model
        )

    def test_uml_model_files_serializer_valid(self):
        serializer = UmlModelFilesSerializer(instance=self.uml_model)
        data = serializer.data
        self.assertEqual(data["id"], self.uml_model.id)
        self.assertEqual(len(data["source_files"]), 1)


class UmlFilesTranslationQueueMessageSerializerTests(TestCase):
    def setUp(self):
        self.uml_model = UmlModel.objects.create(
            name="Test UML Model",
            description="A description"
        )

    def test_uml_files_translation_queue_message_serializer_valid(self):
        context = {
            "ids_of_source_files": [1, 2],
            "ids_of_edited_files": [3],
            "ids_of_new_submitted_files": [4],
            "ids_of_deleted_files": [5]
        }
        serializer = UmlFilesTranslationQueueMessageSerializer(instance=self.uml_model, context=context)
        data = serializer.data
        self.assertEqual(data["ids_of_source_files"], [1, 2])
        self.assertEqual(data["ids_of_edited_files"], [3])
        self.assertEqual(data["ids_of_new_submitted_files"], [4])
        self.assertEqual(data["ids_of_deleted_files"], [5])


class UmlFileTranslationStatusSerializerTests(TestCase):
    def setUp(self):
        self.uml_model = UmlModel.objects.create(
            name="Test UML Model",
            description="A description"
        )
        self.uml_file = UmlFile.objects.create(
            data="<xml>Some UML data</xml>",
            filename="diagram.xmi",
            format=UmlFile.SupportedFormat.EA_XMI,
            state=10,
            model=self.uml_model
        )

    def test_uml_file_translation_status_serializer_valid(self):
        data = {
            "id": self.uml_file.id,
            "state": 20,
            "message": "Translation completed successfully",
            "process_id": "process_123"
        }
        serializer = UmlFileTranslationStatusSerializer(instance=self.uml_file, data=data)
        self.assertTrue(serializer.is_valid())
        updated_file = serializer.save()
        self.assertEqual(updated_file.state, 20)
        self.assertEqual(updated_file.last_process_id, "process_123")

    def test_uml_file_translation_status_serializer_invalid(self):
        data = {
            "id": self.uml_file.id,
            "state": 20,
            "process_id": "process_123"
        }
        serializer = UmlFileTranslationStatusSerializer(instance=self.uml_file, data=data)
        self.assertTrue(serializer.is_valid())
        updated_file = serializer.save()
        self.assertEqual(updated_file.state, 20)
        self.assertEqual(updated_file.last_process_id, "process_123")
