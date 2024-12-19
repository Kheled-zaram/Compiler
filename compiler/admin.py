from django.contrib import admin

# Register your models here.

from .models import Folder, File, FileSection, TabulatorOption, DependantTabulatorOption

admin.site.register(Folder)
admin.site.register(File)
admin.site.register(FileSection)
admin.site.register(TabulatorOption)
admin.site.register(DependantTabulatorOption)