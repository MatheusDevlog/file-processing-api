from io import BytesIO

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient

from file_processing.models import ProcessingJob
from file_processing.processing import (
    process_customer_file,
    read_csv_records,
    read_json_records,
    run_processing_job,
    summarize_customer_records,
    validate_customer_record,
)


@pytest.mark.django_db
def test_creates_pending_processing_job():
    processing_job = ProcessingJob.objects.create(
        original_file='uploads/clientes.csv',
        original_name='clientes.csv',
        file_format=ProcessingJob.FileFormat.CSV,
    )

    saved_processing_job = ProcessingJob.objects.get(pk=processing_job.pk)

    assert saved_processing_job.status == ProcessingJob.Status.PENDING
    assert saved_processing_job.original_name == 'clientes.csv'
    assert saved_processing_job.result is None
    assert saved_processing_job.error_message == ''


@pytest.mark.django_db
def test_rejects_invalid_file_format():
    processing_job = ProcessingJob(
        original_file='uploads/clientes.txt',
        original_name='clientes.txt',
        file_format='txt',
    )

    with pytest.raises(ValidationError) as error:
        processing_job.full_clean()

    assert 'file_format' in error.value.message_dict


@pytest.mark.parametrize(
    'filename, content, expected_format',
    [
        (
            'clientes.csv',
            b'nome,email\nAna,ana@example.com\n',
            ProcessingJob.FileFormat.CSV,
        ),
        (
            'clientes.json',
            b'[{"nome": "Ana", "email": "ana@example.com"}]',
            ProcessingJob.FileFormat.JSON,
        ),
    ],
)
@pytest.mark.django_db
def test_upload_creates_pending_processing_job(
    tmp_path, settings, filename, content, expected_format
):
    settings.MEDIA_ROOT = tmp_path
    uploaded_file = SimpleUploadedFile(filename, content)

    response = APIClient().post(
        reverse('processing-job-upload'),
        {'file': uploaded_file},
        format='multipart',
    )

    assert response.status_code == 201
    processing_job = ProcessingJob.objects.get(pk=response.data['id'])
    assert response.data['status'] == ProcessingJob.Status.PENDING
    assert processing_job.original_name == filename
    assert processing_job.file_format == expected_format
    assert processing_job.status == ProcessingJob.Status.PENDING
    assert (tmp_path / processing_job.original_file.name).read_bytes() == content


@pytest.mark.django_db
def test_upload_rejects_invalid_extension(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    uploaded_file = SimpleUploadedFile('clientes.txt', b'conteudo de exemplo')

    response = APIClient().post(
        reverse('processing-job-upload'),
        {'file': uploaded_file},
        format='multipart',
    )

    assert response.status_code == 400
    assert 'file' in response.data
    assert ProcessingJob.objects.count() == 0
    assert list(tmp_path.iterdir()) == []


@pytest.mark.django_db
def test_upload_rejects_oversized_file(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    content = b'a' * (1024 * 1024 + 1)
    uploaded_file = SimpleUploadedFile('clientes.csv', content)

    response = APIClient().post(
        reverse('processing-job-upload'),
        {'file': uploaded_file},
        format='multipart',
    )

    assert response.status_code == 400
    assert 'file' in response.data
    assert ProcessingJob.objects.count() == 0
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('case', ['missing', 'empty'])
@pytest.mark.django_db
def test_upload_rejects_missing_or_empty_file(tmp_path, settings, case):
    settings.MEDIA_ROOT = tmp_path
    data = {}

    if case == 'empty':
        data['file'] = SimpleUploadedFile('clientes.csv', b'')

    response = APIClient().post(
        reverse('processing-job-upload'),
        data,
        format='multipart',
    )

    assert response.status_code == 400
    assert 'file' in response.data
    assert ProcessingJob.objects.count() == 0
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    'record, expected_fields',
    [
        ({'nome': 'Ana', 'email': 'ana@example.com'}, []),
        ({'nome': ' ', 'email': 'ana@example.com'}, ['nome']),
        ({'nome': 'Ana', 'email': ' '}, ['email']),
        ({'nome': 'Ana'}, ['email']),
        ({'nome': 42, 'email': None}, ['nome', 'email']),
    ],
)
def test_validates_required_customer_fields(record, expected_fields):
    assert validate_customer_record(record) == expected_fields


def test_reads_csv_records():
    file = BytesIO(
        b'nome,email\n'
        b'Ana,ana@example.com\n'
        b'Bia,bia@example.com\n'
    )

    records = read_csv_records(file)

    assert records == [
        {'nome': 'Ana', 'email': 'ana@example.com'},
        {'nome': 'Bia', 'email': 'bia@example.com'},
    ]


@pytest.mark.parametrize(
    'content',
    [
        b'nome,telefone\nAna,123\n',
        b'\n',
    ],
)
def test_rejects_csv_without_required_columns(content):
    file = BytesIO(content)

    with pytest.raises(ValueError, match='CSV deve conter as colunas nome e email.'):
        read_csv_records(file)


def test_reads_json_records():
    file = BytesIO(b'[{"nome": "Ana", "email": "ana@example.com"}]')

    records = read_json_records(file)

    assert records == [{'nome': 'Ana', 'email': 'ana@example.com'}]


@pytest.mark.parametrize(
    'content, message',
    [
        (b'{"nome": "Ana"}', 'lista de registros'),
        (b'[{"nome": "Ana"}, "Bia"]', 'deve ser um objeto'),
    ],
)
def test_rejects_json_with_invalid_structure(content, message):
    file = BytesIO(content)

    with pytest.raises(ValueError, match=message):
        read_json_records(file)


def test_summarizes_valid_and_invalid_records():
    records = [
        {'nome': 'Ana', 'email': 'ana@example.com'},
        {'nome': ' ', 'email': 'bia@example.com'},
        {'nome': '', 'email': ''},
    ]

    summary = summarize_customer_records(records)

    assert summary == {
        'total': 3,
        'validos': 1,
        'invalidos': 2,
        'erros': [
            {'registro': 2, 'campos_invalidos': ['nome']},
            {'registro': 3, 'campos_invalidos': ['nome', 'email']},
        ],
    }


@pytest.mark.parametrize(
    'file_format, content',
    [
        ('csv', b'nome,email\nAna,ana@example.com\nBia,\n'),
        (
            'json',
            b'[{"nome": "Ana", "email": "ana@example.com"},'
            b'{"nome": "Bia", "email": ""}]',
        ),
    ],
)
def test_processes_customer_files(file_format, content):
    file = BytesIO(content)

    summary = process_customer_file(file, file_format)

    assert summary == {
        'total': 2,
        'validos': 1,
        'invalidos': 1,
        'erros': [
            {'registro': 2, 'campos_invalidos': ['email']},
        ],
    }


def test_rejects_unsupported_file_format():
    file = BytesIO(b'conteudo')

    with pytest.raises(ValueError, match='Formato de arquivo não suportado'):
        process_customer_file(file, 'txt')


@pytest.mark.django_db
def test_runs_processing_job_and_saves_result(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    file = SimpleUploadedFile(
        'clientes.csv',
        b'nome,email\nAna,ana@example.com\nBia,\n',
    )
    processing_job = ProcessingJob.objects.create(
        original_file=file,
        original_name=file.name,
        file_format=ProcessingJob.FileFormat.CSV,
    )

    run_processing_job(processing_job)
    processing_job.refresh_from_db()

    assert processing_job.status == ProcessingJob.Status.COMPLETED
    assert processing_job.result == {
        'total': 2,
        'validos': 1,
        'invalidos': 1,
        'erros': [
            {'registro': 2, 'campos_invalidos': ['email']},
        ],
    }
    assert processing_job.error_message == ''


@pytest.mark.django_db
def test_saves_failure_when_csv_lacks_required_columns(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    file = SimpleUploadedFile(
        'clientes.csv',
        b'nome,telefone\nAna,123\n'
    )
    processing_job = ProcessingJob.objects.create(
        original_file=file,
        original_name=file.name,
        file_format=ProcessingJob.FileFormat.CSV,
    )

    run_processing_job(processing_job)
    processing_job.refresh_from_db()

    assert processing_job.status == ProcessingJob.Status.FAILED
    assert processing_job.result is None
    assert processing_job.error_message == 'O CSV deve conter as colunas nome e email.'


@pytest.mark.django_db
def test_saves_failure_when_stored_file_is_missing(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    processing_job = ProcessingJob.objects.create(
        original_file='uploads/inexistente.csv',
        original_name='inexistente.csv',
        file_format=ProcessingJob.FileFormat.CSV,
    )

    run_processing_job(processing_job)
    processing_job.refresh_from_db()

    assert processing_job.status == ProcessingJob.Status.FAILED
    assert processing_job.result is None
    assert processing_job.error_message == 'Não foi possível acessar o arquivo armazenado.'


@pytest.mark.django_db
def test_gets_pending_processing_job():
    processing_job = ProcessingJob.objects.create(
        original_file='uploads/clientes.csv',
        original_name='clientes.csv',
        file_format=ProcessingJob.FileFormat.CSV,
    )

    response = APIClient().get(
        reverse(
            'processing-job-detail',
            kwargs={'pk': processing_job.pk},
        )
    )

    assert response.status_code == 200
    assert response.data == {
        'id': str(processing_job.id),
        'status': ProcessingJob.Status.PENDING,
        'result': None,
        'error_message': '',
    }


@pytest.mark.django_db
def test_returns_404_for_missing_processing_job():
    response = APIClient().get(
        reverse(
            'processing-job-detail',
            kwargs={'pk': '00000000-0000-0000-0000-000000000000'},
        )
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_upload_process_and_get_result(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    uploaded_file = SimpleUploadedFile(
        'clientes.csv',
        b'nome,email\nAna,ana@example.com\nBia,\n',
    )
    client = APIClient()

    upload_response = client.post(
        reverse('processing-job-upload'),
        {'file': uploaded_file},
        format='multipart',
    )
    assert upload_response.status_code == 201
    processing_id = upload_response.data['id']

    processing_response = client.post(
        reverse('processing-job-process', kwargs={'pk': processing_id}),
    )
    detail_response = client.get(
        reverse('processing-job-detail', kwargs={'pk': processing_id}),
    )

    assert processing_response.status_code == 200
    assert processing_response.data == {
        'id': processing_id,
        'status': ProcessingJob.Status.COMPLETED,
    }
    assert detail_response.status_code == 200
    assert detail_response.data['result'] == {
        'total': 2,
        'validos': 1,
        'invalidos': 1,
        'erros': [
            {'registro': 2, 'campos_invalidos': ['email']},
        ],
    }


@pytest.mark.django_db
def test_upload_process_and_get_failure(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    uploaded_file = SimpleUploadedFile(
        'clientes.csv',
        b'nome,telefone\nAna,123\n'
    )
    client = APIClient()

    upload_response = client.post(
        reverse('processing-job-upload'),
        {'file': uploaded_file},
        format='multipart',
    )
    assert upload_response.status_code == 201
    processing_id = upload_response.data['id']

    processing_response = client.post(
        reverse('processing-job-process', kwargs={'pk': processing_id}),
    )
    detail_response = client.get(
        reverse('processing-job-detail', kwargs={'pk': processing_id}),
    )

    assert processing_response.status_code == 200
    assert processing_response.data == {
        'id': processing_id,
        'status': ProcessingJob.Status.FAILED,
    }
    assert detail_response.status_code == 200
    assert detail_response.data == {
        'id': processing_id,
        'status': ProcessingJob.Status.FAILED,
        'result': None,
        'error_message': 'O CSV deve conter as colunas nome e email.',
    }


@pytest.mark.django_db
def test_processing_missing_job_returns_404():
    response = APIClient().post(
        reverse(
            'processing-job-process',
            kwargs={'pk': '00000000-0000-0000-0000-000000000000'},
        ),
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_rejects_reprocessing_completed_job(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    saved_result = {
        'total': 1,
        'validos': 1,
        'invalidos': 0,
        'erros': []
    }
    processing_job = ProcessingJob.objects.create(
        original_file='uploads/inexistente.csv',
        original_name='inexistente.csv',
        file_format=ProcessingJob.FileFormat.CSV,
        status=ProcessingJob.Status.COMPLETED,
        result=saved_result,
    )

    response = APIClient().post(
        reverse('processing-job-process', kwargs={'pk': processing_job.pk}),
    )
    processing_job.refresh_from_db()

    assert response.status_code == 409
    assert response.data == {'detail': 'Este processamento já foi iniciado.'}
    assert processing_job.status == ProcessingJob.Status.COMPLETED
    assert processing_job.result == saved_result
