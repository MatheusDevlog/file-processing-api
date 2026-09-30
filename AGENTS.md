# Instruções para agentes de desenvolvimento

## Contexto e retomada

- No início da sessão, leia `docs/CONTEXTO_DESENVOLVIMENTO.md` e `docs/ESTADO_FILE_PROCESSING.md`, quando existirem, antes de alterar arquivos.
- Esses documentos são privados e ficam ignorados pelo Git. Não copie seu conteúdo pessoal para documentação pública, commits ou PRs.
- Se não estiverem disponíveis, siga este arquivo, consulte o README e inspecione o código. Não presuma o estado da branch, do PR ou das verificações.
- As orientações atuais do usuário prevalecem sobre as regras destes documentos.

## Projeto

- Esta é a File Processing API, um projeto de portfólio para receber arquivos CSV ou JSON, validar registros, processar seu conteúdo e disponibilizar o resultado pela API.
- A stack planejada é Python, Django, Django REST Framework, PostgreSQL, Docker, pytest e pytest-django. Confirme no código e nas dependências o que já foi instalado antes de orientar comandos.
- Mantenha o MVP pequeno: upload, consulta do estado (`pending`, `processing`, `completed`, `failed`), resultado e motivo de falha. Celery e Redis são possibilidades futuras, não requisitos do MVP.

## Colaboração

- Responda em português brasileiro e ajuste as explicações às dúvidas apresentadas.
- Antes de implementar uma parte importante, explique objetivo, arquivos envolvidos e caminho da informação pelo sistema.
- Trabalhe em uma funcionalidade por vez, mantendo código simples, legível e escopo pequeno.
- Use os comandos oficiais das ferramentas para gerar estruturas padrão e executar instalações, migrations e outras tarefas automatizadas; o usuário executa esses comandos no próprio terminal. Explique o papel dos arquivos gerados sem exigir que ele digite ou estude cada linha do código padrão.
- Ao orientar comandos Python neste projeto, use como padrão a venv ativada com `source .venv/bin/activate` no terminal do usuário. Depois, mostre comandos como `python -m pip` e `python manage.py`; use caminhos `.venv/bin/...` apenas quando houver motivo específico.
- Ao preparar um projeto no VS Code, oriente selecionar a `.venv` em `Python: Select Interpreter` para que análise e autocomplete usem o ambiente do projeto. Ao retomar o projeto, lembre de conferir a seleção na barra inferior se o editor não reconhecer os imports. A seleção do editor e a ativação da venv no terminal são passos distintos.
- O usuário quer digitar no editor o código específico da aplicação, dos testes e as alterações necessárias nos arquivos gerados. Apresente instruções e trechos exatos, um arquivo ou bloco pequeno por vez; não edite esses arquivos por ele, salvo pedido explícito. A IA pode revisar os arquivos depois que forem escritos.
- Ao sugerir novos trechos de código Python, use aspas simples por padrão. Use aspas duplas quando a string contiver aspas simples ou isso evitar escapes; use aspas duplas triplas em docstrings. Não altere código já escrito apenas para trocar aspas; arquivos gerados por ferramentas podem manter o estilo gerado.
- Antes de cada trecho, mostre a ordem da implementação, o caminho do arquivo, sua função, a origem dos imports e como ele se conecta aos arquivos já criados e aos próximos. Acompanhe um exemplo concreto pelo caminho da requisição e dos dados.
- Após o usuário escrever um trecho, confira o arquivo e resolva dúvidas ou erros antes de avançar. Não presuma que o código apresentado já foi digitado ou executado.
- Após editar arquivos, explique por arquivo o que mudou, como foi feito, por que existe e como se conecta ao restante do projeto.
- Use linguagem natural e exemplos concretos de uso da API nas explicações de funcionalidades. Relacione a situação real ao caminho da requisição, ao código de cada arquivo e aos efeitos nos dados; explique os termos necessários com detalhe proporcional à mudança.
- O usuário executa comandos de desenvolvimento, instalação, migração, testes, Git e GitHub, salvo pedido explícito para executá-los. A IA pode ler e editar arquivos.
- Ao orientar comandos, informe onde executar, para que servem e o resultado esperado. Peça a saída apenas em caso de erro, diferença ou dúvida.
- Indique claramente a próxima ação. Se houver dúvida sobre o código, esclareça antes de avançar.
- Ao sugerir novas ferramentas, skills ou ajustes no fluxo de trabalho, explique o motivo e o impacto para o usuário avaliar antes de adotá-los. Continue o trabalho já combinado que não depende dessa decisão.
- Ao receber uma nova regra de trabalho, pergunte se ela deve ser registrada no contexto, exceto quando o usuário já pedir o registro. Mantenha este arquivo coerente com as regras essenciais aprovadas.

## Verificação

- Oriente a escrita de testes automatizados relevantes junto da funcionalidade, antes do commit. Cubra sucesso, entradas inválidas e regras importantes; não deixe toda a suíte para o final.
- Quando pytest, pytest-django e o ambiente estiverem configurados, oriente a execução de `python -m pytest -q` com a venv ativada, o PostgreSQL iniciado e as variáveis do `.env` carregadas pelo usuário. Antes disso, confirme o comando adequado à estrutura existente.
- `manage.py check` e migrations são verificações complementares; não substituem testes de comportamento.
- Use Thunder Client como padrão para testes manuais de endpoints. Forneça método, URL, cabeçalhos/autenticação necessários, corpo, status e resposta esperados, incluindo efeitos nos dados quando aplicáveis.
- Testes manuais complementam os automatizados, sem exigir repetição de toda a suíte. Use curl nas orientações manuais somente por solicitação ou necessidade específica de documentação.
- Relate com precisão o que foi executado, o que foi confirmado pelo usuário e o que está pendente.

## Git e entrega

- Use `main` como branch principal; branches de trabalho e mensagens de commit em português. Prefixos como `feat`, `fix`, `test`, `docs` e `chore` podem continuar em inglês.
- Planeje o histórico desde o início: após o planejamento, feche uma primeira etapa pequena com o esqueleto do projeto, `.gitignore`, `README.md` inicial e arquivos públicos necessários. Verifique e revise essa etapa, oriente o primeiro commit e crie/publique o repositório no GitHub antes de acumular funcionalidades.
- Antes de iniciar cada nova funcionalidade, indique qual parte verificável será entregue e quando ocorrerão revisão, teste e commit. Após concluí-la, oriente commit, push, PR e merge conforme o fluxo; não deixe várias funcionalidades prontas sem registrar a evolução no Git.
- O README inicial deve descrever apenas o que já existe. Documentos privados em `docs/` e segredos em `.env` não entram nos commits; `AGENTS.md` e `.env.example` podem ser versionados.
- Para uma funcionalidade concluída, confirme a branch, use git add . na raiz quando todos os arquivos alterados pertencem à entrega, confira uma vez com git status --short, faça o commit e depois o push. Use git add com caminhos específicos quando o commit incluir apenas parte das alterações.
- Use git diff e verificações adicionais de Git quando houver dúvida, conflito, arquivo inesperado ou revisão específica; não os repita como rotina. Após o push de uma branch de trabalho, oriente a abertura e revisão do PR antes do merge.
- Use `git pull` como padrão para atualizar branches que acompanham o remoto. Se houver divergência ou conflito, analise antes de continuar.
- Siga o fluxo: implementar, testar, revisar, commit, push da branch, PR, revisão e merge. Não invente histórico nem publique verificações não realizadas.
- Ao orientar um PR, forneça título, descrição pronta, branch de origem e branch de destino.
- A descrição do PR deve conter alterações e verificações da entrega. Não inclua próximas etapas ou planos futuros; mantenha-os na conversa ou no estado privado do projeto.
- Preserve `.env` e `docs/` fora do versionamento. Não exponha valores secretos nas explicações.
