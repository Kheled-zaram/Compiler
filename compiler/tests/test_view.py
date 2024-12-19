import os

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import SimpleCookie, FileResponse
from django.test import TestCase, Client, override_settings

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser, User
from django.urls import reverse

from AWWW_app import settings
from compiler.forms import DeleteFileForm, UploadFileForm
from compiler.models import TabulatorOption, Tabulator, DependantTabulatorOption, File, Folder
from compiler.views import IndexView, FileDownloadView, CompileView, DeleteFolderFormView
import tempfile


def log_in_and_get_response(view_test_case, view_name, expected_code):
    view_test_case.client.force_login(view_test_case.user)
    response = view_test_case.client.get(reverse(view_name))
    view_test_case.assertEqual(response.status_code, expected_code)
    return response


def get_anonymous(view_test_case, view_name):
    response = view_test_case.client.get(reverse(view_name))
    view_test_case.assertEqual(response.status_code, 302)
    view_test_case.assertRedirects(response, '/accounts/login/?next=' + reverse(view_name))


def post_anonymous(view_test_case, view_name):
    response = view_test_case.client.post(reverse(view_name))
    view_test_case.assertEqual(response.status_code, 302)
    view_test_case.assertRedirects(response, '/accounts/login/?next=' + reverse(view_name))


def post_empty_form(view_test_case, view_name, required_field):
    view_test_case.client.force_login(view_test_case.user)
    response = view_test_case.client.post(reverse(view_name))
    view_test_case.assertEqual(response.status_code, 200)
    form = response.context['form']
    view_test_case.assertIn('This field is required.', form.errors.get(required_field, []))


class IndexViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_get_with_user_logged_in(self):
        log_in_and_get_response(self, 'index', 200)

    def test_get_with_anonymous_user(self):
        get_anonymous(self, 'index')

    def test_post(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('index'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('index'))

    def test_get_tabs(self):
        processor = TabulatorOption.objects.create(form_id=1, name="processor", command="processor_command",
                                                   tab=Tabulator.PROCESSOR.name)
        standard = TabulatorOption.objects.create(form_id=1, name="standard", command="standard_command",
                                                  tab=Tabulator.STANDARD.name)
        optimization = TabulatorOption.objects.create(form_id=1, name="optimization", command="optimization_command",
                                                      tab=Tabulator.OPTIMIZATIONS.name)
        dependant = DependantTabulatorOption.objects.create(form_id=1, name="dependant", command="dependant_command",
                                                            tab=Tabulator.DEPENDANT.name, dependant_from=processor)
        response = log_in_and_get_response(self, 'index', 200)
        self.assertTrue(len(response.context['standard_tab'].fields) == 1)
        self.assertTrue(len(response.context['optimizations_tab'].fields) == 1)
        self.assertTrue(len(response.context['dependant_tab_forms']['1'].fields) == 1)
        self.assertEqual(response.context['dependant_tab_msg'], 'Choose processor from PROCESSOR tab first.')


class ChooseFileViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_get_with_user_logged_in(self):
        log_in_and_get_response(self, 'display_choose_file', 200)

    def test_get_with_anonymous_user(self):
        get_anonymous(self, 'display_choose_file')

    def test_get_files_and_folders(self):
        file = File.objects.create(name="test_file.c", owner=self.user)
        folder = Folder.objects.create(name="test_folder", owner=self.user)
        response = log_in_and_get_response(self, 'display_choose_file', 200)
        self.assertEqual(list(response.context['files']), [file])
        self.assertEqual(list(response.context['folders']), [folder])

    def test_file_in_folder(self):
        folder = Folder.objects.create(name="test_folder", owner=self.user)
        file = File.objects.create(name="test_file.c", owner=self.user, parentFolder=folder)
        response = log_in_and_get_response(self, 'display_choose_file', 200)
        self.assertEqual(list(response.context['files']), [])
        self.assertEqual(list(response.context['folders']), [folder])

    def test_another_user_file(self):
        user = User.objects.create_user(username='testuser2', password='testpassword2')
        file = File.objects.create(name="test_file.c", owner=user)
        response = log_in_and_get_response(self, 'display_choose_file', 200)
        self.assertEqual(list(response.context['files']), [])
        self.assertEqual(list(response.context['folders']), [])


class FileTextViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_get_with_user_logged_in(self):
        log_in_and_get_response(self, 'file_text', 200)

    def test_get_with_anonymous_user(self):
        get_anonymous(self, 'file_text')

    def test_get_files(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b'Test data')

        file = File.objects.create(name="test_file.c", owner=self.user, fileContent=temp_file.name)

        self.client.force_login(self.user)
        response = self.client.get(reverse('file_text'), {'file_id': file.id})
        self.assertEqual(response.status_code, 200)

        os.remove(temp_file.name)

    def test_get_nonexistent_file(self):
        file_id = 9999  # Invalid file ID
        self.client.force_login(self.user)
        response = self.client.get(reverse('file_text'), {'file_id': file_id})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'compiler/file_text.html')
        self.assertNotContains(response, 'Test data')


@override_settings(MEDIA_ROOT='/tmp/media/')
class UploadFileFormViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.url = reverse('upload')

    def test_post_with_anonymous_user(self):
        post_anonymous(self, 'upload')

    def test_post_empty_form(self):
        post_empty_form(self, 'upload', 'fileContent')

    def test_post_valid_form(self):
        self.client.force_login(self.user)
        file_path = 'media/test_file.c'
        with open(file_path, 'rb') as file:
            response = self.client.post(self.url, {'fileContent': file})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('index'), fetch_redirect_response=False)
        self.assertTrue(File.objects.filter(owner=self.user, name='test_file.c').exists())

    def test_post_invalid_form(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'fileContent': 'invalid_data'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'compiler/file_form.html')
        self.assertFormError(response, 'form', 'fileContent', 'This field is required.')


class AddDirectoryFormViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.url = reverse('add-directory')

    def test_post_with_anonymous_user(self):
        post_anonymous(self, 'add-directory')

    def test_post_empty_form(self):
        post_empty_form(self, 'add-directory', 'name')

    def test_post_valid_form(self):
        self.client.force_login(self.user)
        folder_name = 'test_folder'  # Provide a test folder name
        response = self.client.post(self.url, {'name': folder_name})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('index'), fetch_redirect_response=False)
        self.assertTrue(Folder.objects.filter(owner=self.user, name=folder_name).exists())

    def test_post_invalid_form(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'name': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'compiler/file_form.html')
        self.assertFormError(response, 'form', 'name', 'This field is required.')

    def test_post_with_existing_folder_name(self):
        self.client.force_login(self.user)
        folder_name = 'existing_folder'  # Provide the name of an existing folder
        folder = Folder.objects.create(name=folder_name, owner=self.user)
        response = self.client.post(reverse('add-directory'), {'name': folder_name})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'name', 'Folder with this name and location already exists.')


class DeleteFileFormViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.file = File.objects.create(name="test_file.c", owner=self.user)

    def test_post_with_anonymous_user(self):
        post_anonymous(self, 'delete_file')

    def test_post_empty_form(self):
        post_empty_form(self, 'delete_file', 'toBeDeleted')

    def test_post(self):
        form_data = {
            'toBeDeleted': self.file.id,
        }
        self.client.force_login(self.user)
        response = self.client.post(reverse('delete_file'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.file.refresh_from_db()
        self.assertFalse(self.file.available)

    def test_post_invalid_form(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('delete_file'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'compiler/file_form.html')
        self.assertFormError(response, 'form', 'toBeDeleted',
                             ['This field is required.', 'There are no files to delete.'])

    def test_post_nonexistent_file(self):
        form_data = {
            'toBeDeleted': 9999,  # Invalid file ID
        }
        self.client.force_login(self.user)
        response = self.client.post(reverse('delete_file'), data=form_data)
        self.assertEqual(response.status_code, 200)


class DeleteFolderFormViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.folder = Folder.objects.create(name="test_folder", owner=self.user)
        self.url = reverse('delete_folder')

    def test_post_with_anonymous_user(self):
        post_anonymous(self, 'delete_folder')

    def test_post_empty_form(self):
        post_empty_form(self, 'delete_folder', 'toBeDeleted')

    def test_post(self):
        form_data = {
            'toBeDeleted': self.folder.id,
        }
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 302)
        self.folder.refresh_from_db()
        self.assertFalse(self.folder.available)

    def test_post_invalid_form(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'compiler/file_form.html')
        self.assertFormError(response, 'form', 'toBeDeleted',
                             ['This field is required.', 'There are no folders to delete.'])

    def test_post_nonexistent_folder(self):
        form_data = {
            'toBeDeleted': 9999,
        }
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)

    def test_post_with_subfolders(self):
        self.client.force_login(self.user)
        folder = Folder.objects.create(name="test_folder", owner=self.user)
        subfolder = Folder.objects.create(name="subfolder", owner=self.user, parentFolder=folder)
        response = self.client.post(reverse('delete_folder'), {'toBeDeleted': folder.id})
        self.assertEqual(response.status_code, 302)
        folder.refresh_from_db()
        subfolder.refresh_from_db()
        self.assertFalse(folder.available or subfolder.available)


class CompileViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.processor = TabulatorOption.objects.create(form_id=1, name="processor", command="processor_command",
                                                        tab=Tabulator.PROCESSOR.name)
        self.standard = TabulatorOption.objects.create(form_id=1, name="standard", command="standard_command",
                                                       tab=Tabulator.STANDARD.name)
        self.optimization = TabulatorOption.objects.create(form_id=1, name="optimization",
                                                           command="optimization_command",
                                                           tab=Tabulator.OPTIMIZATIONS.name)
        self.dependant = DependantTabulatorOption.objects.create(form_id=1, name="dependant",
                                                                 command="dependant_command",
                                                                 tab=Tabulator.DEPENDANT.name,
                                                                 dependant_from=self.processor)
        self.url = reverse('compile')

    def test_post_with_anonymous_user(self):
        post_anonymous(self, 'compile')

    def test_post_with_file_id(self):
        file = File.objects.create(name='test.c', owner=self.user)
        self.client.force_login(self.user)
        response = self.client.post(self.url, data={'file_id': file.id})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'compiler/compile.html')

    def test_post_flags(self):
        file = File.objects.create(name='test.c', owner=self.user)
        self.client.force_login(self.user)
        data = {
            'file_id': file.id,
            'processor-field': self.processor.form_id,
            'standard-field': self.standard.form_id,
            'optimization-field': self.optimization.form_id,
            'dependant-field': self.dependant.form_id,
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'compiler/compile.html')

    def test_post_with_invalid_file_id(self):
        invalid_file_id = 9999
        self.client.force_login(self.user)
        response = self.client.post(reverse('compile'), {'file_id': invalid_file_id})
        self.assertEqual(response.status_code, 200)


class FileDownloadViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.url = reverse('download')

    def test_post_with_anonymous_user(self):
        post_anonymous(self, 'download')

    def test_get_without_file_id(self):
        request = self.factory.get(self.url)
        request.user = self.user
        response = FileDownloadView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_get_asm_not_exists(self):
        self.client.force_login(self.user)

        file = File.objects.create(name='test.c', owner=self.user)

        self.client.cookies['file_id'] = file.id
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_with_invalid_file_id(self):
        invalid_file_id = 9999  # Invalid file ID
        self.client.force_login(self.user)
        self.client.cookies['file_id'] = invalid_file_id
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
