import pytest

from file_processing.models import ProcessingJob
from file_processing.processing import validar_registro_cliente
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient


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
def test_upload_cria_processamento_pendente(
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
    job = ProcessingJob.objects.get(pk=response.data['id'])
    assert response.data['status'] == ProcessingJob.Status.PENDING
    assert job.original_name == filename
    assert job.file_format == expected_format
    assert job.status == ProcessingJob.Status.PENDING
    assert (tmp_path / job.original_file.name).read_bytes() == content


@pytest.mark.django_db
def test_upload_rejeita_extensao_invalida(tmp_path, settings):
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
def test_upload_rejeita_arquivo_acima_do_limite(tmp_path, settings):
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


@pytest.mark.parametrize('case', ['ausente', 'vazio'])
@pytest.mark.django_db
def test_upload_rejeita_arquivo_ausente_ou_vazio(tmp_path, settings, case):
    settings.MEDIA_ROOT = tmp_path
    data = {}

    if case == 'vazio':
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
    'registro, campos_esperados',
    [
        ({'nome': 'Ana', 'email': 'ana@example.com'}, []),
        ({'nome': ' ', 'email': 'ana@example.com'}, ['nome']),
        ({'nome': 'Ana', 'email': ' '}, ['email']),
        ({'nome': 'Ana'}, ['email']),
        ({'nome': 42, 'email': None}, ['nome', 'email']),
    ],
)
def test_valida_campos_obrigatorios_do_cliente(registro, campos_esperados):
    assert validar_registro_cliente(registro) == campos_esperados
