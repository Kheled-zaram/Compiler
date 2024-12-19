import logging
import os
import subprocess

from django.contrib import messages
from django.http import HttpResponseRedirect, FileResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin

from compiler.forms import UploadFileForm, AddDirectoryForm, DeleteFileForm, DeleteFolderForm, \
    MultipleChoiceForm, OneChoiceForm, ProcessorTabForm
from compiler.models import File, Folder, get_available, compilation_asm_path, compilation_path, file_path, \
    Tabulator, tabulator_option_by_tab_and_form_id, FileOrFolder


class IndexView(LoginRequiredMixin, View):
    template_name = "compiler/index.html"

    def get_context_data(self):
        standard_tab = OneChoiceForm(choices=Tabulator.STANDARD.get_options_to_form(), prefix=Tabulator.STANDARD.name)
        optimizations_tab = MultipleChoiceForm(choices=Tabulator.OPTIMIZATIONS.get_options_to_form(),
                                               prefix=Tabulator.OPTIMIZATIONS.name)
        processor_tab = ProcessorTabForm(prefix=Tabulator.PROCESSOR.name)
        dependant_tab_msg = 'Choose processor from ' + Tabulator.PROCESSOR.name + ' tab first.'

        dependant_tab_forms = {}
        for processor in Tabulator.PROCESSOR.get_options():
            dependant_tab_forms[str(processor.form_id)] = OneChoiceForm(
                choices=Tabulator.DEPENDANT.get_dependant_options_to_form(processor_option=processor),
                prefix=Tabulator.DEPENDANT.name + str(processor.form_id))

        return {'standard_tab': standard_tab,
                'optimizations_tab': optimizations_tab,
                'processor_tab': processor_tab,
                'dependant_tab_forms': dependant_tab_forms,
                'dependant_tab_msg': dependant_tab_msg}

    def get(self, request):
        delete_compilation_files(request.user.id)
        return render(request, self.template_name, self.get_context_data())

    def post(self, request):
        messages.warning(request, 'Choose file and then compile it.')
        return HttpResponseRedirect(reverse('index'))


class ChooseFileView(LoginRequiredMixin, View):
    template_name = "compiler/choose_file.html"

    @staticmethod
    def get_context_data(user_id):
        files = get_available(File, user_id).filter(parentFolder__isnull=True)
        folders = get_available(Folder, user_id).filter(parentFolder__isnull=True)
        return {'files': files,
                'folders': folders}

    def get(self, request):
        delete_compilation_files(request.user.id)
        return render(request, self.template_name, self.get_context_data(user_id=request.user.id))


class FileTextView(LoginRequiredMixin, View):
    template_name = "compiler/file_text.html"

    def get(self, request):
        file_id = request.COOKIES.get('file_id')
        context = {}
        if file_id:
            context = read_file(file_id)
        return render(request, self.template_name, context)


class UploadFileFormView(LoginRequiredMixin, FormView):
    template_name = "compiler/file_form.html"
    form_class = UploadFileForm
    success_url = "/compiler/"
    login_url = "/accounts/login/"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user_id'] = self.request.user.id
        return kwargs

    def form_valid(self, form):
        file = form.save(commit=False)
        file.owner_id = self.request.user.id
        file.name = form.cleaned_data['fileContent'].name
        file.save()
        return super().form_valid(form)


class AddDirectoryFormView(LoginRequiredMixin, FormView):
    template_name = "compiler/file_form.html"
    form_class = AddDirectoryForm
    success_url = "/compiler/"
    login_url = "/accounts/login/"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user_id'] = self.request.user.id
        return kwargs

    def form_valid(self, form):
        folder = form.save(commit=False)
        folder.owner_id = self.request.user.id
        folder.save()
        return super().form_valid(form)


class DeleteFileFormView(LoginRequiredMixin, FormView):
    template_name = "compiler/file_form.html"
    form_class = DeleteFileForm
    success_url = "/compiler/"
    login_url = "/accounts/login/"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user_id'] = self.request.user.id
        return kwargs

    def form_valid(self, form):
        request = self.request

        toBeDeleted = form.cleaned_data.get('toBeDeleted')
        toBeDeleted.available = False
        toBeDeleted.save()
        if isinstance(toBeDeleted, Folder):
            self.delete_subfiles_and_subdirectories(toBeDeleted)

        return super().form_valid(form)


    def delete_subfiles_and_subdirectories(self, toBeDeleted):
        for file in File.objects.filter(parentFolder=toBeDeleted):
            file.available = False
            file.save()
        for folder in Folder.objects.filter(parentFolder=toBeDeleted):
            folder.available = False
            folder.save()
            self.delete_subfiles_and_subdirectories(folder)


class DeleteFolderFormView(DeleteFileFormView):
    form_class = DeleteFolderForm
    login_url = "/accounts/login/"


class CompileView(LoginRequiredMixin, View):
    template_name = "compiler/compile.html"
    login_url = "/accounts/login/"

    def post(self, request):
        file_id = request.COOKIES.get('file_id')
        if not file_id:
            return render(request, self.template_name, {})

        flags = get_flags(request, Tabulator.STANDARD.name, "")
        flags += get_flags(request, Tabulator.OPTIMIZATIONS.name, "")
        processor_options = get_options(request, Tabulator.PROCESSOR.name, "")

        if processor_options is not None:
            processor = processor_options[0]
            flags += processor.command + " "
            flags += get_flags(request, Tabulator.DEPENDANT.name, str(processor.form_id)) + " "
        print(flags)

        context = compile(request, file_id, flags)
        return render(request, self.template_name, context)


class FileDownloadView(LoginRequiredMixin, View):
    login_url = "/accounts/login/"
    template_name = IndexView.template_name

    def get(self, request):
        file_id = request.COOKIES.get('file_id')
        if not file_id or not File.objects.filter(id=file_id).exists():
            return render(request, self.template_name)

        file = File.objects.get(id=file_id)
        asm_path = compilation_asm_path(file)
        if os.path.exists(asm_path):
            filename = os.path.basename(asm_path)
            response = FileResponse(open(asm_path, 'rb'), content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response
        else:
            return render(request, self.template_name)


def get_options(request, name, name_suffix):
    fields = request.POST.get(name + name_suffix + '-field')
    options = []

    if fields is None:
        return None
    elif isinstance(fields, str):
        options.append(tabulator_option_by_tab_and_form_id(name, fields))
    else:
        for field in fields:
            options.append(tabulator_option_by_tab_and_form_id(name, field))
    return options


def get_flags(request, name, name_suffix):
    options = get_options(request, name, name_suffix)
    if options is None:
        return ""
    flags = ""
    for option in options:
        flags += option.command + " "
    return flags


def delete_additional_newlines(lines):
    return [line.strip('\n') for line in lines]


def divide_into_sections(request):
    fileId = request.GET.get('file_id', '')
    if not is_query_valid(fileId):
        return HttpResponseRedirect(reverse('index'))


def is_query_valid(param):
    return param is not None and param != ''


def read_file(file_id):
    if not File.objects.filter(id=file_id).exists():
        return {}

    file = File.objects.get(id=file_id)
    with file.fileContent.open('r') as f:
        text = f.readlines()
    return {'text': delete_additional_newlines(text)}


def compile(request, file_id, flags):
    if not File.objects.filter(id=file_id).exists():
        return {}

    file = File.objects.get(id=file_id)

    asm_path = compilation_asm_path(file)
    os.makedirs(compilation_path(file), exist_ok=True)
    if not flags:
        subprocess_result = subprocess.run(['sdcc', '-S', file_path(file), '-o', asm_path], stderr=subprocess.PIPE)
    else:
        subprocess_result = subprocess.run(['sdcc', flags, '-S', file_path(file), '-o', asm_path],
                                           stderr=subprocess.PIPE)

    context = {}
    if os.path.exists(asm_path):
        with open(asm_path, 'r') as f:
            asm = f.readlines()
        context = {'asm': divide_asm_into_sections(delete_additional_newlines(asm))}
    else:
        messages.warning(request, 'Compilation failure.')
    return context


def divide_asm_into_sections(asm):
    sections = []
    header = None
    content = []
    i = 0
    while i < len(asm):
        line = asm[i]
        if line.startswith(";-"):
            if header is None and i + 2 < len(asm):
                header = [asm[i], asm[i + 1], asm[i + 2]]
                i += 2
            elif header is not None:
                sections.append([header, content])
                header = None
                content = []
                i -= 1
        else:
            content.append(line)
        i += 1
    return sections


def delete_compilation_files(user_id):
    directory = os.path.join('media', str(user_id), 'compilation')
    if os.path.exists(directory):
        for file_name in os.listdir(directory):
            file_path = os.path.join(directory, file_name)
            if os.path.isfile(file_path):
                os.unlink(file_path)
