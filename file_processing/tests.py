import pytest

from file_processing.models import ProcessingJob
from django.core.exceptions import ValidationError


@pytest.mark.django_db
def test_cria_processamento_pendente():
    job = ProcessingJob.objects.create(
        original_file='uploads/clientes.csv',
        original_name='clientes.csv',
        file_format=ProcessingJob.FileFormat.CSV,
    )

    saved_job = ProcessingJob.objects.get(pk=job.pk)

    assert saved_job.status == ProcessingJob.Status.PENDING
    assert saved_job.original_name == 'clientes.csv'
    assert saved_job.result is None
    assert saved_job.error_message == ''


@pytest.mark.django_db
def test_rejeita_formato_invalido():
    job = ProcessingJob(
        original_file='uploads/clientes.txt',
        original_name='clientes.txt',
        file_format='txt',
    )

    with pytest.raises(ValidationError) as error:
        job.full_clean()

    assert 'file_format' in error.value.message_dict
