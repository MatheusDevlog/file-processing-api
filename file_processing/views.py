from pathlib import Path

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from file_processing.models import ProcessingJob
from file_processing.processing import run_processing_job
from file_processing.serializers import ProcessingJobUploadSerializer


class ProcessingJobUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = ProcessingJobUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data['file']
        file_format = Path(uploaded_file.name).suffix.lower().lstrip('.')

        processing_job = ProcessingJob.objects.create(
            original_file=uploaded_file,
            original_name=uploaded_file.name,
            file_format=file_format,
        )

        return Response(
            {'id': str(processing_job.id), 'status': processing_job.status},
            status=status.HTTP_201_CREATED
        )


class ProcessingJobDetailView(APIView):
    def get(self, request, pk):
        processing_job = get_object_or_404(ProcessingJob, pk=pk)

        return Response({
            'id': str(processing_job.id),
            'status': processing_job.status,
            'result': processing_job.result,
            'error_message': processing_job.error_message,
        })


class ProcessingJobProcessView(APIView):
    def post(self, request, pk):
        processing_job = get_object_or_404(ProcessingJob, pk=pk)

        if processing_job.status != ProcessingJob.Status.PENDING:
            return Response(
                {'detail': 'Este processamento já foi iniciado.'},
                status=status.HTTP_409_CONFLICT,
            )

        run_processing_job(processing_job)

        return Response({
            'id': str(processing_job.id),
            'status': processing_job.status,
        })
