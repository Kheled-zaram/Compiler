from django.contrib.auth.models import User
from django.forms import ModelForm, ModelChoiceField, Form, CharField, ChoiceField, RadioSelect, CheckboxSelectMultiple, \
    MultipleChoiceField

from compiler.models import File, Folder, FileOrFolder, get_available, Tabulator


class FileDirectoryForm(ModelForm):
    location = ModelChoiceField(queryset=Folder.objects.none(), required=False)
    owner = None

    class Meta:
        model = FileOrFolder
        fields = ['location']

    def __init__(self, user_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['location'].queryset = get_available(Folder, user_id)
        self.owner = User.objects.get(id=user_id)

        if not self.fields['location'].queryset.exists():
            self.fields.pop('location')

    def save(self, commit=True):
        file_or_folder = super().save(commit=False)
        location = self.cleaned_data.get('location')
        if location:
            file_or_folder.parentFolder = location
        if commit:
            file_or_folder.save()
        return file_or_folder

    def is_valid(self):
        if not super().is_valid():
            return False
        location = self.cleaned_data.get('location')
        if location and not location.available:
            self.add_error('location', 'Selected folder is not available.')
            return False
        name = self.cleaned_data.get('name')
        if Folder.objects.filter(parentFolder=location, owner=self.owner, name=name).exists():
            self.add_error('name', 'Folder with this name and location already exists.')
            return False
        return True


class UploadFileForm(FileDirectoryForm):
    class Meta:
        model = File
        fields = ['fileContent', 'location']


class AddDirectoryForm(FileDirectoryForm):
    class Meta:
        model = Folder
        fields = ['name', 'location']


class DeleteFileForm(Form):
    toBeDeleted = ModelChoiceField(queryset=File.objects.none(), required=True, label='')

    class Meta:
        fields = ['toBeDeleted']

    def __init__(self, user_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['toBeDeleted'].queryset = get_available(File, user_id)

        if not self.fields['toBeDeleted'].queryset.exists():
            self.fields.pop('toBeDeleted')
            self.fields['no_objects'] = CharField(disabled=True, label='No objects found',
                                                  initial='There are no files to delete.')

    def clean(self):
        cleaned_data = super().clean()
        if 'toBeDeleted' not in cleaned_data and 'no_objects' not in self.fields:
            self.add_error('toBeDeleted', 'There are no files to delete.')
        return cleaned_data


class DeleteFolderForm(Form):
    toBeDeleted = ModelChoiceField(queryset=Folder.objects.none(), required=True, label='')

    class Meta:
        model = Folder
        fields = ['toBeDeleted']

    def __init__(self, user_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['toBeDeleted'].queryset = get_available(Folder, user_id)

        if not self.fields['toBeDeleted'].queryset.exists():
            self.fields.pop('toBeDeleted')
            self.fields['no_objects'] = CharField(disabled=True, label='No objects found',
                                                  initial='There are no folders to delete.')

    def clean(self):
        cleaned_data = super().clean()
        if 'toBeDeleted' not in cleaned_data and 'no_objects' not in self.fields:
            self.add_error('toBeDeleted', 'There are no folders to delete.')
        return cleaned_data


class ProcessorTabForm(Form):
    field = ChoiceField(label='', choices=Tabulator.PROCESSOR.get_options_to_form(),
                        widget=RadioSelect(attrs={'onClick': 'processorDependantTab(this.value);'}))


class MultipleChoiceForm(Form):
    field = MultipleChoiceField(widget=CheckboxSelectMultiple, label='')

    def __init__(self, choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['field'].choices = choices


class OneChoiceForm(Form):
    field = ChoiceField(widget=RadioSelect(), label='')

    def __init__(self, choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['field'].choices = choices
