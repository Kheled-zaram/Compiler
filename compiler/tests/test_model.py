from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from compiler.models import File, Folder, FileSection, SectionType, SectionStatus, Tabulator, TabulatorOption, \
    DependantTabulatorOption, tabulator_option_by_tab_and_form_id, file_path, get_available


class FileModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="username", password="password")
        self.file = File.objects.create(name="test_name.c", owner=self.user)
        self.file2 = File.objects.create(name="test_name2.c", owner=self.user)

    def test_model_string(self):
        self.assertEquals(str(self.file), "test_name.c")

    def test_file_path(self):
        self.assertEquals(file_path(self.file), "media/" + str(self.file.owner_id) + "/" + str(self.file.id) + ".c")

    def test_user_to_many_files(self):
        self.assertEquals(File.objects.filter(owner=self.user).count(), 2)

    def test_get_available(self):
        available_files = get_available(File, self.user.id)

        self.assertEqual(available_files.count(), 2)
        self.assertIn(self.file, available_files)
        self.assertIn(self.file2, available_files)

        self.file2.available = False
        self.file2.save()
        available_files = get_available(File, self.user.id)
        self.assertNotIn(self.file2, available_files)


class FolderModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="username", password="password")
        self.folder = Folder.objects.create(name="test_name", owner=self.user)
        self.folder_child = Folder.objects.create(name="test_name2", owner=self.user, parentFolder=self.folder)
        self.file_child = File.objects.create(name="test_name", owner=self.user, parentFolder=self.folder)

    def test_model_string(self):
        self.assertEquals(str(self.folder), "test_name")

    def test_files_property(self):
        self.assertIn(self.file_child, self.folder.files)

    def test_folders_property(self):
        self.assertIn(self.folder_child, self.folder.folders)

    def test_user_to_many_folders(self):
        self.assertEquals(Folder.objects.filter(owner=self.user).count(), 2)

    def test_get_available(self):
        available_folders = get_available(Folder, self.user.id)

        self.assertEqual(available_folders.count(), 2)
        self.assertIn(self.folder, available_folders)
        self.assertIn(self.folder_child, available_folders)

        self.folder_child.available = False
        self.folder_child.save()
        available_folders = get_available(Folder, self.user.id)
        self.assertNotIn(self.folder_child, available_folders)


class FileSectionModelTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="username", password="password")
        self.file = File.objects.create(name="test_name", owner=user)
        self.section = FileSection.objects.create(name="test_section", fileAttached=self.file, type='PROCEDURE',
                                                  status='COMPILATION_SUCCESSFUL')

    def test_model_string(self):
        self.assertEquals(str(self.section), "test_section")

    def test_invalid_type(self):
        self.section.type = "ILLEGAL_TYPE"
        with self.assertRaises(ValidationError):
            self.section.clean_fields()

    def test_invalid_status(self):
        self.section.status = "ILLEGAL_STATUS"
        with self.assertRaises(ValidationError):
            self.section.clean_fields()

    def test_created_date(self):
        self.assertLess(self.section.createdDate, timezone.now())

class SectionTypeModelTests(TestCase):
    def test_section_type_values(self):
        self.assertEqual(SectionType.PROCEDURE, 'PROCEDURE')
        self.assertEqual(SectionType.COMMENT, 'COMMENT')
        self.assertEqual(SectionType.COMPILER_DIRECTIVES, 'COMPILER_DIRECTIVES')
        self.assertEqual(SectionType.VARIABLE_DECLARATION, 'VARIABLE_DECLARATION')
        self.assertEqual(SectionType.INLINE_ASSEMBLY, 'INLINE_ASSEMBLY')


class SectionStatusDataModelTests(TestCase):
    def test_section_status_values(self):
        # Write test cases to check the values of SectionStatus
        self.assertEqual(SectionStatus.COMPILATION_SUCCESSFUL, 'COMPILATION_SUCCESSFUL')
        self.assertEqual(SectionStatus.COMPILATION_WARNINGS, 'COMPILATION_WARNINGS')
        self.assertEqual(SectionStatus.COMPILATION_ERRORS, 'COMPILATION_ERRORS')


class TabulatorOptionTest(TestCase):

    def test_get_options(self):
        tabulator = Tabulator.STANDARD
        options = tabulator.get_options()
        self.assertEqual(options.count(), 0)

    def test_get_options_to_form(self):
        tabulator = Tabulator.OPTIMIZATIONS
        options_to_form = tabulator.get_options_to_form()
        self.assertEqual(len(options_to_form), 0)

    def test_get_dependant_options_to_form(self):
        processor_option = TabulatorOption.objects.create(form_id=1, name='Option 1', command='CMD',
                                                          tab=Tabulator.PROCESSOR)
        dependant_option = DependantTabulatorOption.objects.create(form_id=2, name='Option 2', command='CMD2',
                                                                   tab=Tabulator.PROCESSOR,
                                                                   dependant_from=processor_option)

        tabulator = Tabulator.PROCESSOR
        dependant_options_to_form = tabulator.get_dependant_options_to_form(processor_option)
        self.assertEqual(len(dependant_options_to_form),
                         1)
        self.assertEqual(dependant_options_to_form[0], (2, 'Option 2'))

    def test_tabulator_option_by_tab_and_form_id(self):
        tabulator_option = TabulatorOption.objects.create(form_id=1, name='Option 1', command='CMD',
                                                          tab=Tabulator.STANDARD)

        found_option = tabulator_option_by_tab_and_form_id(Tabulator.STANDARD, 1)
        self.assertEqual(found_option, tabulator_option)

        with self.assertRaises(TabulatorOption.DoesNotExist): tabulator_option_by_tab_and_form_id(
            Tabulator.OPTIMIZATIONS, 1)
