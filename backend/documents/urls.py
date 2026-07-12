from django.urls import path

from .views import (
    DocumentDetailView,
    DocumentDownloadView,
    DocumentListView,
    DocumentUploadView,
    DocumentVerifyView,
)

urlpatterns = [
    path('upload/', DocumentUploadView.as_view(), name='document_upload'),
    path('<uuid:pk>/download/', DocumentDownloadView.as_view(), name='document_download'),
    path('<uuid:pk>/verify/', DocumentVerifyView.as_view(), name='document_verify'),
    path('<uuid:pk>/', DocumentDetailView.as_view(), name='document_detail'),
    path('', DocumentListView.as_view(), name='document_list'),
]
