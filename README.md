# File Processing API

API REST para receber arquivos CSV ou JSON, validar registros e disponibilizar o resultado do processamento.

O projeto está na etapa inicial: a estrutura Django e o PostgreSQL estão configurados. Os endpoints de upload e consulta ainda não foram implementados.

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