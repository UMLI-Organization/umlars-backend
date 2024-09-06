from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from umlars_app.models import UmlModel


class ViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        self.uml_model = UmlModel.objects.create(name="Test Model", description="Test Description")
        self.uml_model.accessed_by.add(self.user)

    def test_home_view_get(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Model")

    def test_login_user_failure(self):
        self.client.logout()  # Ensure no user is logged in
        response = self.client.post(reverse('home'), {
            'username': 'nonexistent_user',
            'password': 'wrong_password',
        })
        self.assertEqual(response.status_code, 302)  # Expect redirect to home
        self.assertRedirects(response, reverse('home'))

    def test_logout_user(self):
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_profile_view(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Profile")

    def test_register_user_success(self):
        self.client.logout()  # Log out the user before registration
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'newpassr4efd43trword123!',
            'password2': 'newpassr4efd43trword123!',
            'email': 'example@em.com',
            'first_name': 'First',
            'last_name': 'Last',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_delete_current_user(self):
        response = self.client.post(reverse('delete-current-user'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))
        self.assertFalse(User.objects.filter(username='testuser').exists())

    def test_delete_uml_model(self):
        response = self.client.post(reverse('delete-uml-model', args=[self.uml_model.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))
        self.assertFalse(UmlModel.objects.filter(id=self.uml_model.id).exists())

    def test_add_uml_model(self):
        response = self.client.get(reverse('add-uml-model'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add UML Model")

    def test_bulk_upload_uml_models(self):
        response = self.client.get(reverse('bulk-upload-uml-models'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bulk Upload UML Models")

    def test_update_uml_model(self):
        response = self.client.post(reverse('update-uml-model', args=[self.uml_model.id]), {
            'name': 'Updated Test Model',
        })
        self.assertEqual(response.status_code, 200)
        self.uml_model.refresh_from_db()
        self.assertEqual(self.uml_model.name, 'Updated Test Model')

    def test_review_bulk_upload_uml_models(self):
        response = self.client.get(reverse('review-bulk-upload-uml-models'))
        self.assertEqual(response.status_code, 200)

    def test_translate_uml_model(self):
        response = self.client.post(reverse('translate-uml-model', args=[self.uml_model.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_share_model(self):
        new_user = User.objects.create_user(username='newuser', password='newpassword')
        response = self.client.post(reverse('share-model', args=[self.uml_model.id]), {
            'user': new_user.id,
        })
        self.assertEqual(response.status_code, 302)

    def test_unshare_model(self):
        new_user = User.objects.create_user(username='newuser', password='newpassword')
        self.uml_model.accessed_by.add(new_user)
        response = self.client.post(reverse('unshare-model', args=[self.uml_model.id, new_user.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.uml_model.accessed_by.filter(id=new_user.id).exists())
