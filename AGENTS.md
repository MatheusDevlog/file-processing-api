# Diretrizes de desenvolvimento

## Contexto

- Este arquivo orienta contribuições à File Processing API. Consulte `README.md` e o código antes de propor mudanças.
- Se existirem documentos locais em `docs/`, consulte-os para retomar o trabalho. Eles são privados, ignorados pelo Git e não devem ser copiados para arquivos públicos, commits ou PRs. Este arquivo deve continuar útil sem eles.

## Projeto e arquitetura

- O objetivo da API é receber arquivos CSV ou JSON, validar registros, processar seu conteúdo e disponibilizar estado, resultado ou motivo de falha.
- A stack atual inclui Python, Django, Django REST Framework, PostgreSQL, Docker Compose, pytest e pytest-django. Confira versões e configuração nos arquivos do projeto antes de orientar comandos.
- Mantenha o MVP pequeno: upload, estados `pending`, `processing`, `completed` e `failed`, resultado e erro. Celery e Redis são possibilidades futuras.
- Prefira responsabilidades claras, funções simples e validações explícitas. Evite dependências ou camadas sem necessidade concreta.
- Use os comandos oficiais do Django e das demais ferramentas para gerar estruturas padrão, instalar dependências e executar migrations.

## Código e documentação

- Em código novo do projeto, prefira nomes claros em português para funções, variáveis, parâmetros e testes. Preserve nomes exigidos por Python, Django, DRF e outras bibliotecas, além dos campos da API já definidos.
- Em novos trechos Python, use aspas simples por padrão; use aspas duplas quando facilitarem a leitura e aspas duplas triplas em docstrings. Preserve o estilo de arquivos gerados e não altere código existente apenas para trocar aspas.
- Mantenha o `README.md` alinhado ao comportamento implementado. Descreva endpoints, configuração, execução e testes sem apresentar funcionalidades futuras como prontas.
- Não publique segredos, valores do `.env`, arquivos enviados ou conteúdo dos documentos privados em `docs/`.

## Verificação

- Escreva testes de comportamento junto da parte implementada: sucesso, entradas inválidas e regras relevantes. `manage.py check` e migrations complementam os testes, sem substituí-los.
- Com a venv ativada, PostgreSQL iniciado e variáveis do `.env` carregadas, execute `python -m pytest -q` conforme as instruções do README.
- Para testes manuais de endpoints, use o cliente de API Bruno API Client. Em uploads, envie `multipart/form-data` com o campo `file` do tipo arquivo e deixe o cliente definir `Content-Type`. Registre método, URL, corpo, status, resposta e efeito esperado.
- Diferencie verificações executadas de resultados informados por outra pessoa. Não declare testes ou operações de Git como realizados sem evidência.

## Git e entrega

- Use `main` como branch principal e uma branch de trabalho por funcionalidade. Use português nos nomes de branches e mensagens de commit; prefixos como `feat`, `fix`, `test`, `docs` e `chore` podem permanecer em inglês.
- Faça commits durante a branch após partes lógicas testadas e revisadas. Código e testes da mesma parte podem entrar juntos; a PR reúne a funcionalidade para revisão e merge.
- Antes de preparar um commit, confira se os arquivos pertencem àquela parte. Faça push da branch antes da PR e apresente na descrição apenas alterações e verificações realizadas.
- Preserve `.env`, `docs/`, `.venv/` e `media/` fora dos commits. Se houver divergência ou conflito ao atualizar uma branch, analise antes de continuar.
