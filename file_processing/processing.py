import csv
import json
from io import StringIO

from file_processing.models import ProcessingJob


def validate_customer_record(record):
    invalid_fields = []

    for field in ('nome', 'email'):
        value = record.get(field)

        if not isinstance(value, str) or not value.strip():
            invalid_fields.append(field)

    return invalid_fields


def read_csv_records(file):
    file.seek(0)
    content = file.read().decode('utf-8-sig')
    reader = csv.DictReader(StringIO(content, newline=''))
    columns = reader.fieldnames or []
    if 'nome' not in columns or 'email' not in columns:
        raise ValueError('O CSV deve conter as colunas nome e email.')
    return list(reader)


def read_json_records(file):
    file.seek(0)
    content = file.read().decode('utf-8-sig')
    records = json.loads(content)

    if not isinstance(records, list):
        raise ValueError('O JSON deve conter uma lista de registros.')

    for record in records:
        if not isinstance(record, dict):
            raise ValueError('Cada registro do JSON deve ser um objeto.')

    return records


def summarize_customer_records(records):
    errors = []

    for record_number, record in enumerate(records, start=1):
        invalid_fields = validate_customer_record(record)

        if invalid_fields:
            errors.append({
                'registro': record_number,
                'campos_invalidos': invalid_fields,
            })

    total_count = len(records)
    invalid_count = len(errors)

    return {
        'total': total_count,
        'validos': total_count - invalid_count,
        'invalidos': invalid_count,
        'erros': errors,
    }


def process_customer_file(file, file_format):
    if file_format == 'csv':
        records = read_csv_records(file)

    elif file_format == 'json':
        records = read_json_records(file)

    else:
        raise ValueError('Formato de arquivo não suportado.')

    return summarize_customer_records(records)


def run_processing_job(processing_job):
    processing_job.status = ProcessingJob.Status.PROCESSING
    processing_job.save(update_fields=['status', 'updated_at'])

    try:
        with processing_job.original_file.open('rb') as file:
            result = process_customer_file(file, processing_job.file_format)

    except (ValueError, OSError) as error:
        if isinstance(error, OSError):
            message = 'Não foi possível acessar o arquivo armazenado.'
        else:
            message = str(error)

        processing_job.result = None
        processing_job.error_message = message
        processing_job.status = ProcessingJob.Status.FAILED
        processing_job.save(update_fields=['result', 'error_message', 'status', 'updated_at'])
        return processing_job

    processing_job.result = result
    processing_job.error_message = ''
    processing_job.status = ProcessingJob.Status.COMPLETED
    processing_job.save(update_fields=['result', 'error_message', 'status', 'updated_at'])

    return processing_job
