import csv
import json
from io import StringIO


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
