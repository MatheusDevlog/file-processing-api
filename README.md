# File Processing API

API REST para receber arquivos CSV ou JSON, validar registros e disponibilizar o resultado do processamento.

O upload, o processamento e a consulta por identificador estão disponíveis. Cada envio cria um `ProcessingJob` com estado `pending`. Uma segunda requisição inicia o processamento do arquivo salvo; a consulta mostra o estado, o resultado ou o erro.

## Tecnologias

Python, Django, Django REST Framework, PostgreSQL, Docker Compose, pytest e pytest-django.

## Configuração local

Crie e ative a venv, depois instale as dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Copie `.env.example` para `.env` e substitua os valores de `DJANGO_SECRET_KEY` e `POSTGRES_PASSWORD`. Em seguida, na raiz do projeto:

```bash
set -a
source .env
set +a
docker compose up -d db
python manage.py migrate
python manage.py check
```

O Django roda na venv local; o PostgreSQL roda no contêiner Docker. O arquivo `.env` contém valores privados e não é versionado.

Para iniciar a API no mesmo terminal, execute:

```bash
python manage.py runserver
```

## Envio de arquivo

Envie uma requisição `POST` para `http://127.0.0.1:8000/api/processamentos/` com corpo `multipart/form-data`. O campo deve se chamar `file` e conter um arquivo CSV ou JSON. Na extensão Bruno API Client, selecione **Body → Multipart Form**, defina `file` como tipo **File** e escolha o arquivo. O cliente configura o cabeçalho `Content-Type`.

O arquivo precisa ter uma extensão `.csv` ou `.json`, não pode estar vazio e deve ter no máximo 1 MiB. A extensão é verificada pelo nome do arquivo; o conteúdo dos registros é validado somente quando o processamento é iniciado.

Um envio aceito retorna `201 Created`:

```json
{
  "id": "efeb1ff5-6d41-4b10-a948-cdd4f263c6e1",
  "status": "pending"
}
```

O identificador muda a cada envio. O arquivo é salvo em `media/uploads/`, e o registro do processamento fica no PostgreSQL. Arquivo ausente, vazio, com extensão não aceita ou acima do limite recebe `400 Bad Request`, sem criar o processamento. Para testar arquivo ausente no Bruno, selecione **No Body**.

## Início do processamento

Depois do upload, envie uma requisição `POST` sem corpo para `http://127.0.0.1:8000/api/processamentos/<id>/processar/`, substituindo `<id>` pelo identificador recebido. No Bruno API Client, selecione **No Body**. A requisição processa o arquivo de modo síncrono: a resposta chega após a leitura e a validação dos registros.

Para um arquivo cuja estrutura pode ser processada, a resposta é `200 OK`:

```json
{
  "id": "efeb1ff5-6d41-4b10-a948-cdd4f263c6e1",
  "status": "completed"
}
```

Se o conteúdo não puder ser processado, o HTTP continua em `200 OK`, mas o estado retornado é `failed`; consulte o recurso para ver `error_message`. Um identificador inexistente retorna `404 Not Found`. Uma nova tentativa para um processamento que não está `pending` retorna `409 Conflict` com a mensagem `Este processamento já foi iniciado.`.

## Consulta de processamento

Envie uma requisição `GET` para `http://127.0.0.1:8000/api/processamentos/<id>/`, substituindo `<id>` pelo identificador retornado no upload. Um processamento recém-criado retorna `200 OK`:

```json
{
  "id": "efeb1ff5-6d41-4b10-a948-cdd4f263c6e1",
  "status": "pending",
  "result": null,
  "error_message": ""
}
```

A consulta mostra o estado, o resultado e a mensagem de erro registrados no banco. Depois de um processamento concluído, `result` contém `total`, `validos`, `invalidos` e `erros`; cada erro informa o número do registro e os campos inválidos. Registros com campos ausentes são contados como inválidos sem mudar o estado `completed`. Se o processamento falhar, `result` é `null` e `error_message` descreve a falha. Um identificador inexistente retorna `404 Not Found`. O upload não inicia o processamento automaticamente.

## Testes

Com a venv ativada, o PostgreSQL iniciado e as variáveis do `.env` carregadas, execute:

```bash
python -m pytest -q
```

Os testes cobrem o modelo, uploads CSV e JSON, rejeições de arquivos inválidos, a lógica de processamento isolada e o fluxo HTTP completo: upload, processamento com sucesso ou falha, consulta, ID inexistente e tentativa repetida.
