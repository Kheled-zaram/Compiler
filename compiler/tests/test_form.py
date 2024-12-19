from django.contrib.auth.models import User
from django.test import TestCase, override_settings, Client
from compiler.forms import UploadFileForm, AddDirectoryForm, DeleteFileForm, DeleteFolderForm
from compiler.models import Folder, File
from django.core.files.uploadedfile import SimpleUploadedFile

@override_settings(MEDIA_ROOT='/tmp/media/')
class UploadFileFormTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.folder = Folder.objects.create(name="test_folder", owner=self.user)

    def test_upload_file_form(self):
        form_data = {
            'location': self.folder,
        }
        file_content = b'Test file content'  # Bytes representing the file content
        uploaded_file = SimpleUploadedFile('test.txt', file_content)
        form = UploadFileForm(user_id=self.user.id, data=form_data, files={'fileContent': uploaded_file})
        self.assertTrue(form.is_valid())
        file_instance = form.save(commit=False)
        file_instance.owner = self.user
        file_instance.save()
        self.assertIsNotNone(file_instance)


class AddDirectoryFormTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.folder = Folder.objects.create(name="test_folder", owner=self.user)

    def test_add_directory_form(self):
        form_data = {
            'name': 'Test Folder',
            'location': self.folder,
        }
        form = AddDirectoryForm(user_id=self.user.id, data=form_data)
        self.assertTrue(form.is_valid())
        folder_instance = form.save(commit=False)
        folder_instance.owner = self.user
        folder_instance.save()
        self.assertIsNotNone(folder_instance)

    def test_add_directory_form_no_available_locations(self):
        form_data = {
            'name': 'New Folder',
            'location': self.folder,
        }
        self.folder.available = False
        self.folder.save()
        form = AddDirectoryForm(user_id=self.user.id, data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.get('location'), None)

class DeleteFileFormTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.file = File.objects.create(name="test_file.c", owner=self.user)

    def test_delete_file_form(self):
        form_data = {
            'toBeDeleted': self.file,
        }
        form = DeleteFileForm(user_id=self.user.id, data=form_data)
        self.assertTrue(form.is_valid())


class DeleteFolderFormTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.folder = Folder.objects.create(name="test_folder", owner=self.user)

    def test_delete_folder_form(self):
        form_data = {
            'toBeDeleted': self.folder,
        }
        form = DeleteFolderForm(user_id=self.user.id, data=form_data)
        self.assertTrue(form.is_valid())
