from django.test import TestCase
from django.contrib.auth.models import User
from umlars_app.forms import (
    SignUpForm, EditUserForm, ChangePasswordForm,
    AddUmlModelForm, UpdateUmlModelForm, AddUmlFileForm, ShareModelForm
)
from umlars_app.models import UmlModel, UmlFile, UserAccessToModel


class SignUpFormTests(TestCase):
    def test_signup_form_valid(self):
        form_data = {
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password1": "password123@!#$rfdsvcx",
            "password2": "password123@!#$rfdsvcx",
        }
        form = SignUpForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_signup_form_invalid_password_mismatch(self):
        form_data = {
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password1": "password123",
            "password2": "password321",
        }
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())


class EditUserFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')

    def test_edit_user_form_valid(self):
        form_data = {
            "username": "testuser",
            "first_name": "Updated",
            "last_name": "User",
            "email": "updated@example.com",
        }
        form = EditUserForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_edit_user_form_invalid_email(self):
        form_data = {
            "username": "testuser",
            "first_name": "Updated",
            "last_name": "User",
            "email": "not-an-email",
        }
        form = EditUserForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())


class ChangePasswordFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')

    def test_change_password_form_valid(self):
        form_data = {
            "old_password": "password123",
            "new_password1": "newpassword123",
            "new_password2": "newpassword123",
        }
        form = ChangePasswordForm(user=self.user, data=form_data)
        self.assertTrue(form.is_valid())

    def test_change_password_form_invalid_mismatch(self):
        form_data = {
            "old_password": "password123",
            "new_password1": "newpassword123",
            "new_password2": "differentpassword123",
        }
        form = ChangePasswordForm(user=self.user, data=form_data)
        self.assertFalse(form.is_valid())


class AddUmlModelFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')

    def test_add_uml_model_form_valid(self):
        form_data = {
            "name": "Test UML Model",
            "description": "A description of the UML model.",
        }
        form = AddUmlModelForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_add_uml_model_form_no_name(self):
        form_data = {
            "description": "A description of the UML model.",
        }
        form = AddUmlModelForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())


class UpdateUmlModelFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.uml_model = UmlModel.objects.create(name="Test UML Model", description="A description")

    def test_update_uml_model_form_valid(self):
        form_data = {
            "name": "Updated UML Model",
            "description": "An updated description.",
        }
        form = UpdateUmlModelForm(data=form_data, instance=self.uml_model)
        self.assertTrue(form.is_valid())

    def test_update_uml_model_form_no_name(self):
        form_data = {
            "description": "An updated description.",
        }
        form = UpdateUmlModelForm(data=form_data, instance=self.uml_model)
        self.assertFalse(form.is_valid())


class AddUmlFileFormTests(TestCase):
    def setUp(self):
        self.uml_model = UmlModel.objects.create(name="Test UML Model", description="A description")

    def test_add_uml_file_form_valid(self):
        form_data = {
            "data": "<xml>Some UML data</xml>",
            "format": UmlFile.SupportedFormat.EA_XMI,
            "filename": "diagram.xmi",
        }
        form = AddUmlFileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_add_uml_file_form_no_data(self):
        form_data = {
            "format": UmlFile.SupportedFormat.EA_XMI,
            "filename": "diagram.xmi",
        }
        form = AddUmlFileForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("You must provide either a source file or formatted data.", form.errors['__all__'])


class ShareModelFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.uml_model = UmlModel.objects.create(name="Test UML Model", description="A description")

    def test_share_model_form_valid(self):
        form_data = {
            "user": self.user.id,
        }
        form = ShareModelForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_share_model_form_invalid_user(self):
        form_data = {
            "user": 999,  # Invalid user ID
        }
        form = ShareModelForm(data=form_data)
        self.assertFalse(form.is_valid())
