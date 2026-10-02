from pathlib import Path

from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from file_processing.models import ProcessingJob
from file_processing.serializers import ProcessingJobUploadSerializer

class ProcessingJobUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = ProcessingJobUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data['file']
        file_format = Path(uploaded_file.name).suffix.lower().lstrip('.')

        job = ProcessingJob.objects.create(
            original_file=uploaded_file,
            original_name=uploaded_file.name,
            file_format=file_format,
        )

        return Response(
            {'id': str(job.id), 'status': job.status},
            status=status.HTTP_201_CREATED
        )