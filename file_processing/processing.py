def validar_registro_cliente(registro):
    campos_invalidos = []

    for campo in ('nome', 'email'):
        valor = registro.get(campo)

        if not isinstance(valor, str) or not valor.strip():
            campos_invalidos.append(campo)

    return campos_invalidos
