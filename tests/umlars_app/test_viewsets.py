from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth.models import User
from umlars_app.models import UmlModel, UmlFile

class UmlModelViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpassword')
        self.uml_model = UmlModel.objects.create(name="Test Model", description="Test description")
        self.uml_model.accessed_by.add(self.user)
        self.client = APIClient()
        self.client.login(username='testuser', password='password')

    def test_list_uml_models(self):
        url = reverse('rest_viewsets:models-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_uml_model(self):
        url = reverse('rest_viewsets:models-detail', args=[self.uml_model.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.uml_model.name)

    def test_create_uml_model(self):
        url = reverse('rest_viewsets:models-list')
        data = {"name": "New Model", "description": "New description"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UmlModel.objects.count(), 2)

    def test_update_uml_model(self):
        url = reverse('rest_viewsets:models-detail', args=[self.uml_model.id])
        data = {"name": "Updated Model", "description": "Updated description"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.uml_model.refresh_from_db()
        self.assertEqual(self.uml_model.name, "Updated Model")

    def test_delete_uml_model(self):
        url = reverse('rest_viewsets:models-detail', args=[self.uml_model.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UmlModel.objects.count(), 0)

    def test_admin_can_access_all_models(self):
        self.client.logout()
        self.client.login(username='admin', password='adminpassword')
        url = reverse('rest_viewsets:models-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), UmlModel.objects.count())


class UmlFileViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpassword')
        self.uml_model = UmlModel.objects.create(name="Test Model", description="Test description")
        self.uml_model.accessed_by.add(self.user)
        self.uml_file = UmlFile.objects.create(
            data="<xml>Some UML data</xml>",
            filename="diagram.xmi",
            format=UmlFile.SupportedFormat.EA_XMI,
            state=10,
            model=self.uml_model
        )
        self.client = APIClient()
        self.client.login(username='testuser', password='password')

    def test_list_uml_files(self):
        url = reverse('rest_viewsets:files-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_uml_file(self):
        url = reverse('rest_viewsets:files-detail', args=[self.uml_file.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['filename'], self.uml_file.filename)


    def test_update_uml_file(self):
        url = reverse('rest_viewsets:files-detail', args=[self.uml_file.id])
        data = {
            "data": "<xml>Updated UML data</xml>",
            "filename": "updated_diagram.xmi",
            "format": UmlFile.SupportedFormat.EA_XMI,
            "state": 20
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.uml_file.refresh_from_db()
        self.assertEqual(self.uml_file.filename, "updated_diagram.xmi")

    def test_delete_uml_file(self):
        url = reverse('rest_viewsets:files-detail', args=[self.uml_file.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UmlFile.objects.count(), 0)

    def test_admin_can_access_all_files(self):
        self.client.logout()
        self.client.login(username='admin', password='adminpassword')
        url = reverse('rest_viewsets:files-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), UmlFile.objects.count())


class UmlModelFilesViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpassword')
        self.uml_model = UmlModel.objects.create(name="Test Model", description="Test description")
        self.uml_model.accessed_by.add(self.user)
        self.uml_file = UmlFile.objects.create(
            data="<xml>Some UML data</xml>",
            filename="diagram.xmi",
            format=UmlFile.SupportedFormat.EA_XMI,
            state=10,
            model=self.uml_model
        )
        self.client = APIClient()
        self.client.login(username='testuser', password='password')

    def test_list_uml_model_files(self):
        url = reverse('rest_viewsets:model-files-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_uml_model_files(self):
        url = reverse('rest_viewsets:model-files-detail', args=[self.uml_model.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['source_files']), 1)


    def test_admin_can_access_all_model_files(self):
        self.client.logout()
        self.client.login(username='admin', password='adminpassword')
        url = reverse('rest_viewsets:model-files-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), UmlModel.objects.count())
