import uuid

from django.db import models


class ProcessingJob(models.Model):
    class FileFormat(models.TextChoices):
        CSV = "csv", "CSV"
        JSON = "json", "JSON"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        PROCESSING = "processing", "Processando"
        COMPLETED = "completed", "Concluído"
        FAILED = "failed", "Falhou"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_file = models.FileField(upload_to="uploads/")
    original_name = models.CharField(max_length=255)
    file_format = models.CharField(max_length=4, choices=FileFormat.choices)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    result = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
