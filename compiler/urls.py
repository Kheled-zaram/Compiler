from django.conf.urls.static import static
from django.urls import path

from AWWW_app import settings
from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('display_choose_file/', views.ChooseFileView.as_view(), name='display_choose_file'),
    path('upload/', views.UploadFileFormView.as_view(), name='upload'),
    path('add_directory/', views.AddDirectoryFormView.as_view(), name='add-directory'),
    path('delete_file/', views.DeleteFileFormView.as_view(), name='delete_file'),
    path('delete_folder/', views.DeleteFolderFormView.as_view(), name='delete_folder'),
    path('divide_into_sections/', views.divide_into_sections, name='divide_into_sections'),
    path('file/', views.FileTextView.as_view(), name='file_text'),
    path('compile/', views.CompileView.as_view(), name='compile'),
    path('file/download/', views.FileDownloadView.as_view(), name='download'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
