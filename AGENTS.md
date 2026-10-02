# Guia técnico para agentes de desenvolvimento

## Fontes e escopo

- Este repositório contém um MVP em desenvolvimento. Consulte `README.md` para o contrato público e os comandos de execução; confira o código antes de propor mudanças.
- Quando existirem, consulte `docs/CONTEXTO_DESENVOLVIMENTO.md` para preferências privadas de colaboração e `docs/ESTADO_FILE_PROCESSING.md` para o estado recente. Esses documentos não fazem parte do repositório público e não devem ser copiados para commits ou PRs.
- Inspecione o código e o estado atual do Git antes de presumir que uma funcionalidade, teste, branch ou entrega já existe.
- Mantenha mudanças pequenas e relacionadas ao pedido. Preserve o comportamento existente fora do escopo da alteração.

## Arquitetura e contrato

- A aplicação usa Python, Django 5.2, Django REST Framework e PostgreSQL. `compose.yaml` inicia somente o banco; a API e os testes executam no Python local da `.venv`. `config/settings.py` lê variáveis de ambiente e configura o armazenamento local em `media/`.
- `config/urls.py` inclui `file_processing/urls.py`. A rota `POST /api/processamentos/` chega à view em `file_processing/views.py`, que usa `MultiPartParser` para receber o formulário com o arquivo.
- `file_processing/serializers.py` exige o campo `file`, aceita apenas nomes terminados em `.csv` ou `.json` e limita o arquivo a 1 MiB. O campo também rejeita arquivos vazios. A verificação da extensão não confirma o conteúdo ou o tipo real do arquivo.
- A view salva o arquivo em `media/uploads/` e cria no PostgreSQL um `ProcessingJob` com estado `pending`; responde `201` com `id` e `status`. `file_processing/models.py` define o UUID, os dados do arquivo, os estados `pending`, `processing`, `completed` e `failed`, o resultado JSON e a mensagem de erro. Mudanças nesse esquema exigem migration em `file_processing/migrations/`.
- `file_processing/processing.py` contém uma função para identificar campos obrigatórios ausentes, vazios ou que não sejam texto em um registro de cliente. Ela ainda não está ligada ao upload. Leitura e processamento de CSV/JSON, transições de estado e consulta do resultado ainda não existem; não os apresente como funcionalidades prontas.

## Convenções de implementação

- Prefira recursos existentes do Django e do DRF antes de acrescentar abstrações ou dependências. Mantenha a validação da entrada no serializer, a coordenação da requisição na view e os dados persistidos no model. Coloque a lógica de processamento em funções próprias quando for implementada.
- Mantenha o MVP pequeno. Celery e Redis não fazem parte da implementação atual.
- Crie migrations quando o esquema dos models mudar, não apenas por alterações em views, serializers ou funções de processamento. Revise os arquivos gerados antes de aplicá-los.
- Em código novo do projeto, prefira nomes claros em português para funções, variáveis, parâmetros e testes. Preserve nomes exigidos por Python, Django e DRF e os campos da API. Use aspas simples por padrão em novos trechos Python; preserve o estilo dos arquivos gerados.
- Atualize o README quando o contrato HTTP, a configuração ou a forma real de executar o projeto mudar.

## Segurança e dados locais

- O endpoint de upload não exige autenticação própria. Não descreva o MVP como protegido por autenticação ou pronto para receber arquivos de terceiros sem outras salvaguardas.
- Preserve as validações atuais de presença, arquivo não vazio, extensão e limite de 1 MiB ao alterar o upload. Não atribua à checagem da extensão uma validação do conteúdo ou da estrutura dos registros.
- Mantenha `.env`, `.venv/`, `docs/` e `media/` fora do versionamento. Use `.env.example` somente como modelo; não publique segredos, arquivos enviados ou dados privados em código, documentação ou PRs.

## Verificação

- Acrescente ou ajuste testes de comportamento em `file_processing/tests.py` junto de cada alteração. Cubra sucesso, entradas inválidas e efeitos no banco e no armazenamento; quando houver consulta por identificador, cubra também o recurso inexistente.
- Os testes usam pytest e pytest-django, configurados em `pytest.ini`. Com a venv ativada, PostgreSQL iniciado e variáveis do `.env` carregadas, execute `python -m pytest -q`.
- `manage.py check` e verificações de migrations ajudam a conferir configuração e esquema, mas não substituem testes de comportamento.
- Para verificações manuais de endpoints, use o cliente de API Bruno API Client. Em uploads, envie `multipart/form-data` com `file` do tipo arquivo e deixe o cliente definir `Content-Type`. Registre método, URL, corpo, status, resposta e efeitos observados.
- Diferencie verificações executadas de resultados informados por outra pessoa. Não declare testes ou operações de Git como realizados sem evidência.

## Git e entrega

- `main` é a branch principal. Desenvolva funcionalidades em branches de trabalho, faça commits por partes lógicas testadas e revisadas e abra PR antes do merge. Use português nos nomes de branches e mensagens de commit; prefixos como `feat`, `fix`, `test`, `docs` e `chore` podem permanecer em inglês.
- Confira os arquivos preparados antes de cada commit. Faça push da branch antes da PR; descreva na PR apenas alterações e verificações efetivas, sem incluir planos futuros.
- Não faça commit, push, merge ou publicação sem a autorização aplicável. Verifique o estado do Git antes de orientar comandos que dependam da branch ou do remoto.
- Preserve arquivos privados fora dos commits. Se houver divergência ou conflito ao atualizar uma branch, analise antes de continuar.
