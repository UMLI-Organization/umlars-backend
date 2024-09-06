from django.test import TestCase
from django.contrib.auth.models import User
from umlars_app.models import UmlModel, UmlFile, UserAccessToModel, ProcessStatus, ObjectAccessLevel
from datetime import datetime


class UmlModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.uml_model = UmlModel.objects.create(
            name="Test UML Model",
            description="A description of the UML model."
        )

    def test_string_representation(self):
        self.assertEqual(str(self.uml_model), "Test UML Model")

    def test_archive_method(self):
        self.uml_model.archive()
        self.assertFalse(self.uml_model.tech_active_flag)
        self.assertIsNotNone(self.uml_model.tech_valid_to)


class UmlFileTests(TestCase):

    def setUp(self):
        self.uml_model = UmlModel.objects.create(
            name="Test UML Model",
            description="A description of the UML model."
        )
        self.uml_file = UmlFile.objects.create(
            data="<xml>Some UML data</xml>",
            filename="diagram.xmi",
            format=UmlFile.SupportedFormat.EA_XMI,
            model=self.uml_model
        )

    def test_string_representation(self):
        expected_str = f"File: diagram.xmi for model Test UML Model in format {self.uml_file.format}"
        self.assertEqual(str(self.uml_file), expected_str)

    def test_default_state(self):
        self.assertEqual(self.uml_file.state, ProcessStatus.QUEUED)

    def test_file_association_with_model(self):
        self.assertEqual(self.uml_file.model, self.uml_model)
        self.assertIn(self.uml_file, self.uml_model.source_files.all())


class UserAccessToModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.uml_model = UmlModel.objects.create(
            name="Test UML Model",
            description="A description of the UML model."
        )
        self.access_record = UserAccessToModel.objects.create(
            user=self.user,
            model=self.uml_model,
            access_level=ObjectAccessLevel.READ
        )

    def test_string_representation(self):
        expected_str = f"User {self.user} has access to model {self.uml_model}"
        self.assertEqual(str(self.access_record), expected_str)

    def test_default_access_level(self):
        access_record = UserAccessToModel.objects.create(
            user=self.user,
            model=self.uml_model,
        )
        self.assertEqual(access_record.access_level, ObjectAccessLevel.WRITE)

    def test_user_access_association_with_model(self):
        self.assertEqual(self.access_record.user, self.user)
        self.assertEqual(self.access_record.model, self.uml_model)
        self.assertIn(self.access_record, UserAccessToModel.objects.filter(user=self.user))


class SCD2ModelTests(TestCase):
    
    def setUp(self):
        self.uml_model = UmlModel.objects.create(
            name="Test UML Model",
            description="A description of the UML model."
        )

    def test_archive_method(self):
        self.uml_model.archive()
        self.assertFalse(self.uml_model.tech_active_flag)
        self.assertIsNotNone(self.uml_model.tech_valid_to)
        self.assertLessEqual(self.uml_model.tech_valid_to, datetime.now())

    def test_tech_valid_from(self):
        self.assertIsNotNone(self.uml_model.tech_valid_from)


class EnumTests(TestCase):

    def test_object_access_level_choices(self):
        self.assertEqual(ObjectAccessLevel.READ, 10)
        self.assertEqual(ObjectAccessLevel.WRITE, 20)

    def test_process_status_choices(self):
        self.assertEqual(ProcessStatus.QUEUED, 10)
        self.assertEqual(ProcessStatus.RUNNING, 20)
        self.assertEqual(ProcessStatus.FINISHED, 30)
        self.assertEqual(ProcessStatus.PARTIAL_SUCCESS, 40)
        self.assertEqual(ProcessStatus.FAILED, 50)
