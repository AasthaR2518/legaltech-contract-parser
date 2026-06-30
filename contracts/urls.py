from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.document_upload_view, name='document-upload'),
    path('', views.document_list_view, name='document-list'),
    path('<uuid:pk>/', views.document_detail_view, name='document-detail'),
    path('<uuid:pk>/download/', views.document_download_zip_view, name='document-download-zip'),
]
