import pytest

from io import BytesIO
from file_processing.models import ProcessingJob
from file_processing.processing import (
    executar_processamento,
    ler_registros_csv,
    ler_registros_json,
    processar_arquivo_clientes,
    resumir_registros_clientes,
    validar_registro_cliente,
)
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


def test_le_registros_csv():
    arquivo = BytesIO(
        b'nome,email\n'
        b'Ana,ana@example.com\n'
        b'Bia,bia@example.com\n'
    )

    registros = ler_registros_csv(arquivo)

    assert registros == [
        {'nome': 'Ana', 'email': 'ana@example.com'},
        {'nome': 'Bia', 'email': 'bia@example.com'},
    ]


@pytest.mark.parametrize(
    'conteudo',
    [
        b'nome,telefone\nAna,123\n',
        b'\n',
    ],
)
def test_rejeita_csv_sem_colunas_obrigatorias(conteudo):
    arquivo = BytesIO(conteudo)

    with pytest.raises(ValueError, match='CSV deve conter as colunas nome e email.'):
        ler_registros_csv(arquivo)


def test_le_registros_json():
    arquivo = BytesIO(b'[{"nome": "Ana", "email": "ana@example.com"}]')

    registros = ler_registros_json(arquivo)

    assert registros == [{'nome': 'Ana', 'email': 'ana@example.com'}]


@pytest.mark.parametrize(
    'conteudo, mensagem',
    [
        (b'{"nome": "Ana"}', 'lista de registros'),
        (b'[{"nome": "Ana"}, "Bia"]', 'deve ser um objeto'),
    ],
)
def test_rejeita_json_com_estrutura_invalida(conteudo, mensagem):
    arquivo = BytesIO(conteudo)

    with pytest.raises(ValueError, match=mensagem):
        ler_registros_json(arquivo)


def test_resume_registros_validos_e_invalidos():
    registros = [
        {'nome': 'Ana', 'email': 'ana@example.com'},
        {'nome': ' ', 'email': 'bia@example.com'},
        {'nome': '', 'email': ''},
    ]

    resumo = resumir_registros_clientes(registros)

    assert resumo == {
        'total': 3,
        'validos': 1,
        'invalidos': 2,
        'erros': [
            {'registro': 2, 'campos_invalidos': ['nome']},
            {'registro': 3, 'campos_invalidos': ['nome', 'email']},
        ],
    }


@pytest.mark.parametrize(
    'formato, conteudo',
    [
        ('csv', b'nome,email\nAna,ana@example.com\nBia,\n'),
        (
            'json',
            b'[{"nome": "Ana", "email": "ana@example.com"},'
            b'{"nome": "Bia", "email": ""}]',
        ),
    ],
)
def test_processa_arquivos_clientes(formato, conteudo):
    arquivo = BytesIO(conteudo)

    resumo = processar_arquivo_clientes(arquivo, formato)

    assert resumo == {
        'total': 2,
        'validos': 1,
        'invalidos': 1,
        'erros': [
            {'registro': 2, 'campos_invalidos': ['email']},
        ],
    }


def test_rejeita_formato_de_arquivo_nao_suportado():
    arquivo = BytesIO(b'conteudo')

    with pytest.raises(ValueError, match='Formato de arquivo não suportado'):
        processar_arquivo_clientes(arquivo, 'txt')


@pytest.mark.django_db
def test_executa_processamento_e_salva_resultado(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    arquivo = SimpleUploadedFile(
        'clientes.csv',
        b'nome,email\nAna,ana@example.com\nBia,\n',
    )
    job = ProcessingJob.objects.create(
        original_file=arquivo,
        original_name=arquivo.name,
        file_format=ProcessingJob.FileFormat.CSV,
    )

    executar_processamento(job)
    job.refresh_from_db()

    assert job.status == ProcessingJob.Status.COMPLETED
    assert job.result == {
        'total': 2,
        'validos': 1,
        'invalidos': 1,
        'erros': [
            {'registro': 2, 'campos_invalidos': ['email']},
        ],
    }
    assert job.error_message == ''
