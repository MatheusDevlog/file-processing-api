import csv
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
