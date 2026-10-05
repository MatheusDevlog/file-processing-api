import csv
import json
from io import StringIO

from file_processing.models import ProcessingJob


def validar_registro_cliente(registro):
    campos_invalidos = []

    for campo in ('nome', 'email'):
        valor = registro.get(campo)

        if not isinstance(valor, str) or not valor.strip():
            campos_invalidos.append(campo)

    return campos_invalidos


def ler_registros_csv(arquivo):
    arquivo.seek(0)
    conteudo = arquivo.read().decode('utf-8-sig')
    leitor = csv.DictReader(StringIO(conteudo, newline=''))
    colunas = leitor.fieldnames or []
    if 'nome' not in colunas or 'email' not in colunas:
        raise ValueError('O CSV deve conter as colunas nome e email.')
    return list(leitor)


def ler_registros_json(arquivo):
    arquivo.seek(0)
    conteudo = arquivo.read().decode('utf-8-sig')
    registros = json.loads(conteudo)

    if not isinstance(registros, list):
        raise ValueError('O JSON deve conter uma lista de registros.')

    for registro in registros:
        if not isinstance(registro, dict):
            raise ValueError('Cada registro do JSON deve ser um objeto.')

    return registros


def resumir_registros_clientes(registros):
    erros = []

    for numero, registro in enumerate(registros, start=1):
        campos_invalidos = validar_registro_cliente(registro)

        if campos_invalidos:
            erros.append({
                'registro': numero,
                'campos_invalidos': campos_invalidos,
            })

    total = len(registros)
    invalidos = len(erros)

    return {
        'total': total,
        'validos': total - invalidos,
        'invalidos': invalidos,
        'erros': erros,
    }


def processar_arquivo_clientes(arquivo, formato):
    if formato == 'csv':
        registros = ler_registros_csv(arquivo)

    elif formato == 'json':
        registros = ler_registros_json(arquivo)

    else:
        raise ValueError('Formato de arquivo não suportado.')

    return resumir_registros_clientes(registros)


def executar_processamento(job):
    job.status = ProcessingJob.Status.PROCESSING
    job.save(update_fields=['status', 'updated_at'])

    try:
        with job.original_file.open('rb') as arquivo:
            resultado = processar_arquivo_clientes(arquivo, job.file_format)

    except ValueError as erro:
        job.result = None
        job.error_message = str(erro)
        job.status = ProcessingJob.Status.FAILED
        job.save(update_fields=['result', 'error_message', 'status', 'updated_at'])
        return job

    job.result = resultado
    job.error_message = ''
    job.status = ProcessingJob.Status.COMPLETED
    job.save(update_fields=['result', 'error_message', 'status', 'updated_at'])

    return job
