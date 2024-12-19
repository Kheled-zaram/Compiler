import os
from enum import Enum

from django.db import models
from django.contrib.auth.models import User


class FileSystem(models.Model):
    name = models.CharField(max_length=100)
    createdDate = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class FileOrFolder(FileSystem):
    parentFolder = models.ForeignKey('Folder', on_delete=models.CASCADE, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, )
    available = models.BooleanField(default=True)
    availabilityEditedDate = models.DateTimeField(auto_now_add=True)
    editedDate = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


def upload_dir(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return '{0}/{1}'.format(instance.owner.id, str(instance.id) + os.path.splitext(filename)[1])


def file_path(instance):
    return 'media/' + upload_dir(instance, instance.name)


def compilation_path(instance):
    return 'media/{0}/compilation'.format(instance.owner.id)


def compilation_asm_path(instance):
    return compilation_path(instance) + '/{1}'.format(instance.owner.id, str(instance.id) + ".asm")


def get_available(file_or_folder_class, owner_id):
    return file_or_folder_class.objects.filter(owner_id=owner_id, available=True)


class File(FileOrFolder):
    fileContent = models.FileField(upload_to=upload_dir)


class Folder(FileOrFolder):
    @property
    def files(self):
        return get_available(File, self.owner_id).filter(parentFolder=self)

    @property
    def folders(self):
        return get_available(Folder, self.owner_id).filter(parentFolder=self)


class SectionType(models.Model):
    PROCEDURE = 'PROCEDURE'
    COMMENT = 'COMMENT'
    COMPILER_DIRECTIVES = 'COMPILER_DIRECTIVES'
    VARIABLE_DECLARATION = 'VARIABLE_DECLARATION'
    INLINE_ASSEMBLY = 'INLINE_ASSEMBLY'

    CHOICES = (
        (PROCEDURE, 'PROCEDURE'),
        (COMMENT, 'COMMENT'),
        (COMPILER_DIRECTIVES, 'COMPILER_DIRECTIVES'),
        (VARIABLE_DECLARATION, 'VARIABLE_DECLARATION'),
        (INLINE_ASSEMBLY, 'INLINE_ASSEMBLY'),
    )


class SectionStatus(models.Model):
    COMPILATION_SUCCESSFUL = 'COMPILATION_SUCCESSFUL'
    COMPILATION_WARNINGS = 'COMPILATION_WARNINGS'
    COMPILATION_ERRORS = 'COMPILATION_ERRORS'

    CHOICES = ((COMPILATION_SUCCESSFUL, 'COMPILATION_SUCCESSFUL'),
              (COMPILATION_WARNINGS, 'COMPILATION_WARNINGS'),
              (COMPILATION_ERRORS, 'COMPILATION_ERRORS'))


# Sekcje mogą mieć podsekcje
class FileSection(FileSystem):
    fileAttached = models.ForeignKey('File', on_delete=models.CASCADE)
    parentSection = models.ForeignKey('FileSection', on_delete=models.CASCADE, null=True)
    sectionBeginning = models.IntegerField
    sectionEnd = models.IntegerField
    type = models.CharField(max_length=20, choices=SectionType.CHOICES)
    status =  models.CharField(max_length=30, choices=SectionStatus.CHOICES)
    statusDetails = models.TextField

    def __str__(self):
        return self.name


class SectionStatusData(models.Model):
    line = models.IntegerField
    message = models.TextField
    section = models.ForeignKey('FileSection', on_delete=models.CASCADE)


class Tabulator(Enum):
    STANDARD = 'STANDARD'
    OPTIMIZATIONS = 'OPTIMIZATIONS'
    PROCESSOR = 'PROCESSOR'
    DEPENDANT = 'DEPENDANT'

    is_multiple_choice = (
        (STANDARD, False),
        (OPTIMIZATIONS, True),
        (PROCESSOR, False),
        (DEPENDANT, False)
    )

    def get_options(self):
        return TabulatorOption.objects.filter(tab=self.name)

    def get_options_to_form(self):
        return self.get_options().values_list('form_id', 'name')

    def get_dependant_options_to_form(self, processor_option):
        return DependantTabulatorOption.objects.filter(dependant_from=processor_option).values_list('form_id', 'name')


class TabulatorOption(models.Model):
    form_id = models.IntegerField()
    name = models.CharField(max_length=40)
    command = models.CharField(max_length=20)
    tab = models.CharField(choices=[(tab_type.name, tab_type.name) for tab_type in Tabulator], max_length=20)

    class Meta:
        unique_together = ('form_id', 'tab')

    def __str__(self):
        return self.name


def tabulator_option_by_tab_and_form_id(tab_name, form_id):
    return TabulatorOption.objects.get(tab=tab_name, form_id=form_id)


class DependantTabulatorOption(TabulatorOption):
    dependant_from = models.ForeignKey(TabulatorOption, on_delete=models.CASCADE, related_name='dependent_options')
