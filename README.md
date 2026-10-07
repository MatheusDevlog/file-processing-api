# File Processing API

API REST para enviar arquivos CSV ou JSON com registros de clientes, validar o conteúdo e consultar um resumo do processamento. O MVP está concluído.

O fluxo tem três requisições: **enviar o arquivo**, **iniciar o processamento** e **consultar o resultado**. O upload não processa o conteúdo automaticamente. O processamento é síncrono: a resposta chega depois da leitura do arquivo.

## Tecnologias

Python, Django 5.2, Django REST Framework, PostgreSQL, Docker Compose, pytest e pytest-django. O Docker Compose inicia somente o PostgreSQL; a API executa no Python local.

## Executar localmente

Na raiz do projeto, crie a venv, ative-a e instale as dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Copie `.env.example` para `.env` e substitua os valores de `DJANGO_SECRET_KEY` e `POSTGRES_PASSWORD`. O `.env` é local e não é versionado.

Carregue as variáveis, inicie o banco e aplique as migrations:

```bash
set -a
source .env
set +a
docker compose up -d db
python manage.py migrate
python manage.py check
```

No mesmo terminal, inicie a API:

```bash
python manage.py runserver
```

O servidor de desenvolvimento fica em `http://127.0.0.1:8000/`. O arquivo enviado é armazenado em `media/uploads/`; o estado e o resumo ficam no PostgreSQL.

## Endpoints

| Método e rota | Ação | Resposta principal |
| --- | --- | --- |
| `POST /api/processamentos/` | Recebe um arquivo no campo `file` | `201` com `id` e `status: "pending"` |
| `POST /api/processamentos/<id>/processar/` | Lê o arquivo salvo e grava resultado ou erro | `200` com `id` e estado final |
| `GET /api/processamentos/<id>/` | Consulta os dados já gravados | `200` com estado, resultado e mensagem de erro |

`<id>` representa o UUID recebido no upload. O mesmo identificador é usado nas outras duas rotas.

## Exemplo: enviar, processar e consultar

Considere este `clientes.csv`:

```csv
nome,email
Ana,ana@example.com
Bia,
```

No Bruno API Client, faça `POST http://127.0.0.1:8000/api/processamentos/` com **Body → Multipart Form**. Adicione uma linha do tipo arquivo, coloque `file` em **Key** e selecione `clientes.csv` em **Value**. Deixe o Bruno definir o `Content-Type`. Se ele restringir caminhos externos, mantenha o arquivo na pasta da coleção.

O upload aceito retorna `201 Created`:

```json
{
  "id": "efeb1ff5-6d41-4b10-a948-cdd4f263c6e1",
  "status": "pending"
}
```

O `id` muda a cada envio. Nesse ponto, a API validou a presença, o tamanho e a extensão do arquivo, mas ainda não leu os registros.

Depois, faça `POST http://127.0.0.1:8000/api/processamentos/<id>/processar/` com **No Body**. Substitua `<id>` pelo valor recebido. A resposta de sucesso é `200 OK`:

```json
{
  "id": "efeb1ff5-6d41-4b10-a948-cdd4f263c6e1",
  "status": "completed"
}
```

Por fim, faça `GET http://127.0.0.1:8000/api/processamentos/<id>/`. A resposta mostra o resumo salvo:

```json
{
  "id": "efeb1ff5-6d41-4b10-a948-cdd4f263c6e1",
  "status": "completed",
  "result": {
    "total": 2,
    "validos": 1,
    "invalidos": 1,
    "erros": [
      {
        "registro": 2,
        "campos_invalidos": ["email"]
      }
    ]
  },
  "error_message": ""
}
```

A linha de Bia conta como registro inválido porque `email` está vazio. Isso não impede o arquivo de terminar com estado `completed`. O `GET` apenas lê o resultado no banco; ele não processa o arquivo novamente.

## Validação, estados e erros

No **upload**, o campo `file` é obrigatório. O arquivo não pode estar vazio, deve ter no máximo **1 MiB** e seu nome precisa terminar em `.csv` ou `.json`. Uma entrada rejeitada retorna `400 Bad Request` sem criar o processamento. A extensão é verificada pelo nome, não pelo tipo real do conteúdo.

No **processamento**, CSV e JSON são lidos como UTF-8. O CSV precisa ter as colunas `nome` e `email`. O JSON precisa conter uma lista de objetos. Em cada registro, `nome` e `email` devem ser textos não vazios. Campos extras são aceitos, mas não são usados no resumo.

Os estados são `pending` (aguardando), `processing` (em execução), `completed` (resumo salvo) e `failed` (erro salvo). Uma linha com campo vazio entra em `invalidos`. Já um CSV sem coluna obrigatória, JSON malformado ou arquivo fora de UTF-8 deixa o processamento em `failed`, com `result: null` e uma explicação em `error_message`.

A chamada `POST /processar/` retorna **HTTP 200** mesmo quando a tentativa termina com estado `failed`; consulte o `GET` para ver o motivo. Um identificador inexistente retorna **404**. Tentar iniciar novamente um processamento que não está `pending` retorna **409 Conflict**.

## Organização do código

- `config/urls.py` e `file_processing/urls.py` ligam as rotas às views.
- `file_processing/views.py` coordena upload, processamento e consulta.
- `file_processing/serializers.py` valida o arquivo recebido no upload.
- `file_processing/processing.py` lê CSV/JSON, valida registros e grava o resultado ou a falha.
- `file_processing/models.py` define o `ProcessingJob` persistido no PostgreSQL.
- `file_processing/tests.py` cobre regras isoladas e o fluxo completo da API.

Os arquivos enviados ficam em `media/`, fora do Git. Não há frontend neste repositório, autenticação própria nem processamento em fila com Celery ou Redis. O armazenamento local e o servidor `runserver` atendem ao desenvolvimento do MVP; a API não está configurada para receber arquivos de terceiros em produção.

## Testes

Com a venv ativa, PostgreSQL iniciado e variáveis do `.env` carregadas, execute:

```bash
python -m pytest -q
```

A suíte cobre upload válido e inválido, leitura de CSV e JSON, validação de registros, estados, falhas, consulta por ID e tentativa de reprocessamento.

## Licença

Distribuído sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE).
