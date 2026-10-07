from django.urls import path

from file_processing.views import (
    ProcessingJobDetailView,
    ProcessingJobUploadView,
    ProcessingJobProcessView
)


urlpatterns = [
    path(
        'processamentos/',
        ProcessingJobUploadView.as_view(),
        name='processing-job-upload',
    ),
    path(
        'processamentos/<uuid:pk>/',
        ProcessingJobDetailView.as_view(),
        name='processing-job-detail',
    ),
    path(
        'processamentos/<uuid:pk>/processar/',
        ProcessingJobProcessView.as_view(),
        name='processing-job-process',
    ),
]
