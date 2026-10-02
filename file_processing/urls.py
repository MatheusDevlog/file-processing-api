from django.urls import path

from file_processing.views import ProcessingJobUploadView


urlpatterns = [
    path(
        'processamentos/',
        ProcessingJobUploadView.as_view(),
        name='processing-job-upload',
    ),
]
