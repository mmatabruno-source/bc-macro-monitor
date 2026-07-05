<!--
Sync Impact Report
Version change: 1.0.0 → 2.0.0
Modified principles:
  - I. Spec-Driven Development, Sem Exceções → I. Spec-Driven Development em
    Duas Trilhas (redefinição incompatível: deixa de ser incondicional para
    todo commit; passa a distinguir trilha completa de trilha leve)
  - III. Isolamento Total Entre os Três Fluxos → III. Isolamento Total Entre
    os Fluxos (atualizado de três para quatro fluxos; nome genérico para não
    exigir nova emenda a cada fluxo novo)
  - IV. Notificação por Bot Dedicado, Sem Bot Padrão → IV. Notificação por
    Bot Dedicado por Domínio Temático (redefinição incompatível: a proibição
    absoluta de compartilhar bot vira uma regra com exceção documentada e
    registrada por escrito, refletindo a decisão já em produção do fluxo 004)
Added sections:
  - Princípio X: Portão de CI Automatizado
Removed sections: none
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ (Constitution Check genérico, sem mudança necessária)
  - .specify/templates/spec-template.md ✅ (sem placeholders específicos de constituição)
  - .specify/templates/tasks-template.md ✅ (categorização já genérica)
  - README.md ⚠ pendente (atualizar para listar os 4 fluxos, não 3)
Follow-up TODOs:
  - Sincronizar specs/002, specs/003 e specs/004 com o estado real do código
    (endpoint RPM, análise em 2 seções, detalhamento por item do IPCA,
    formato de setas do Resumo Focus) — rastreado fora desta constituição.
-->

# bc-macro-monitor Constitution

## Core Principles

### I. Spec-Driven Development em Duas Trilhas (NON-NEGOTIABLE quanto à escolha de trilha)
Toda mudança de código MUST ser conscientemente classificada em uma de duas
trilhas antes de ser implementada — a escolha em si não é opcional, ainda
que o caminho completo não seja sempre obrigatório:

- **Trilha completa** (`/speckit-specify` → `/speckit-plan` →
  `/speckit-tasks` → `/speckit-implement`): MUST ser usada para qualquer
  feature nova, qualquer mudança de contrato de API externa, qualquer
  mudança de modelo de dados (`data-model.md`) ou de requisito funcional
  (FR) já documentado. Cada commit resultante MUST referenciar o ID da
  tarefa de `tasks.md` que resolve.
- **Trilha leve** (edição direta): MAY ser usada para ajustes cosméticos de
  mensagem/formatação, correções de bug que não alteram contrato ou FR, e
  mudanças de configuração (ex.: horário de cron, timeouts). Toda mudança
  pela trilha leve MUST, ainda assim, deixar um registro objetivo no
  `research.md` (ou changelog equivalente) da feature afetada — o quê
  mudou e por quê — e o commit/PR MUST citar qual `specs/NNN-*` ela toca.

Qualquer ambiguidade sobre qual trilha usar MUST ser resolvida perguntando
explicitamente ao usuário antes de implementar — nunca decidida em silêncio
pelo agente. É PROIBIDO tratar a trilha leve como "pular o processo": ela é
um caminho legítimo e documentado, não uma exceção informal.
**Racional**: a versão anterior deste princípio (trilha única, incondicional)
não sobreviveu ao contato com a realidade — na prática, ajustes pequenos e
testes em produção sempre foram feitos por edição direta, sem que a
constituição refletisse isso, gerando divergência silenciosa entre specs e
código ao longo de várias iterações. Nomear as duas trilhas explicitamente
não abre mão de rigor onde ele importa (contratos, FRs, modelos de dados) e
elimina a divergência não-intencional em tudo o mais.

### II. Nunca Codificar Contra um Contrato de API Não Verificado (NON-NEGOTIABLE)
Para CADA endpoint externo novo que qualquer fluxo deste projeto vier a
consumir é PROIBIDO escrever qualquer cliente HTTP, parser ou modelo de
dados antes de o usuário colar a resposta JSON real de uma chamada de teste
executada de fato (navegador, curl, Postman, ou uma chamada real disparada
via GitHub Actions). O arquivo `contracts/*.md` correspondente só pode ser
escrito a partir do payload real observado. Documentação de terceiros,
exemplos de blog ou "formato razoável esperado" NUNCA são fonte válida para
o contrato. Se o payload real ainda não foi fornecido, a tarefa
correspondente MUST ficar bloqueada e o agente MUST parar e pedir
explicitamente ao usuário que cole a resposta de teste antes de prosseguir.
Isso vale também quando um endpoint já verificado muda de comportamento em
produção (ex.: dataset renomeado ou congelado) — o novo payload MUST ser
verificado da mesma forma antes de corrigir o contrato.
**Racional**: no projeto irmão, o primeiro contrato para a API de
Comunicados do BCB foi escrito com base numa hipótese não verificada e teve
que ser reescrito após testar no navegador — o custo de verificar antes é
sempre menor que o custo de descobrir depois, em produção. Neste projeto,
o mesmo padrão de risco se confirmou quando o dataset do Relatório de
Política Monetária foi renomeado (`ri/relatorios` → `rpm/relatorios`) sem
aviso, e só foi descoberto por observação de comportamento estagnado em
produção.

### III. Isolamento Total Entre os Fluxos
Todos os fluxos deste projeto (hoje: Focus/Copom, Relatório de Política
Monetária, IPCA, e Resumo Semanal do Focus) MUST ser tratados como unidades
de falha independentes dentro da mesma execução agendada. Uma exceção não
tratada em um fluxo MUST ser capturada, logada e notificada ao bot daquele
fluxo especificamente, e MUST NUNCA impedir a checagem, o processamento ou
a notificação dos demais fluxos na mesma execução. Cada fluxo tem sua
própria chave de estado em `estado.json` e seu próprio diretório de
histórico (`historico/<fluxo>/`), para que uma corrupção ou erro de leitura
em um não contamine os demais. A adição de um novo fluxo MUST seguir o
mesmo padrão de isolamento e NUNCA MUST exigir uma emenda a este princípio
— ele é intencionalmente escrito de forma genérica para não ficar
desatualizado a cada fluxo novo.

### IV. Notificação por Bot Dedicado por Domínio Temático
Cada fluxo publica em um bot/chat do Telegram próprio (token e chat_id
independentes, via GitHub Secrets), por padrão. Compartilhar um bot entre
dois fluxos MAY ocorrer apenas quando (a) os fluxos pertencem ao mesmo
domínio temático (ex.: Focus/Copom e Resumo Semanal do Focus, ambos sobre
expectativas de mercado), (b) a decisão for explícita do usuário, e (c) a
exceção for registrada por escrito no `plan.md`/`spec.md` da feature que
introduz o compartilhamento, citando qual bot é reaproveitado e por quê.
Fora dessa exceção documentada, não existe bot "padrão" ou de fallback
compartilhado. Toda função de notificação — inclusive `notificar_falha` —
MUST receber explicitamente qual bot/chat pertence ao fluxo que está
reportando, e MUST NUNCA enviar o aviso de falha de um fluxo para o bot de
outro fluxo de domínio temático diferente.
**Racional**: a versão anterior deste princípio proibia compartilhamento de
forma absoluta, mas o fluxo do Resumo Semanal do Focus já reaproveita o bot
do Focus/Copom em produção, por decisão do usuário — a regra escrita
contradizia a prática real. Nomear a exceção explicitamente (em vez de
ignorá-la ou proibi-la sem efeito) resolve a divergência.

### V. Idempotência de Publicação
Nenhuma publicação já processada MUST gerar uma segunda notificação. O
registro de "processado" em `estado.json` só MUST ser gravado DEPOIS que o
envio ao Telegram for confirmado como bem-sucedido (HTTP 2xx). Se a
notificação falhar, o estado MUST permanecer como "não processado" para
que a próxima execução tente novamente — falhar ao notificar nunca pode
ser confundido com falhar ao processar. Este comportamento MUST ter teste
automatizado dedicado por fluxo (não apenas cobertura indireta via teste de
falha na busca de dados) — ver Princípio X.

### VI. API Oficial como Única Fonte de Verdade
A fonte de verdade de cada fluxo MUST ser sempre a API oficial
correspondente, nunca um calendário de datas estimadas de publicação. Um
calendário MAY ser usado para ajustar a frequência ou o horário de checagem
(ex.: adiar o cron para depois do horário oficial de divulgação de uma
fonte apertada), mas MUST NUNCA ser usado para decidir se um fluxo verifica
ou deixa de verificar a API naquela execução.

### VII. Simplicidade Sobre Otimização Prematura
Entre duas soluções corretas, a mais simples MUST vencer. É PROIBIDO
introduzir filas, workers, bancos de dados externos ou frameworks
adicionais além do necessário para os fluxos existentes. Armazenamento
MUST permanecer em arquivos JSON e Markdown versionados no próprio
repositório Git. Abstrações genéricas antecipando fluxos futuros
hipotéticos MUST ser evitadas — construir para os fluxos existentes, não
para "fluxos futuros".

### VIII. Resiliência de Rede e de Notificação
Toda chamada HTTP externa MUST usar retry seletivo: retentar em 429
(respeitando o header `Retry-After` quando presente) e em 5xx
(indisponibilidade transitória), e MUST NUNCA retentar em outros códigos
4xx (ex.: 404), que são permanentes. Todo envio ao Telegram MUST ter
fallback de formatação — se o Markdown for rejeitado (HTTP 400 com erro de
parsing de entidades), o sistema MUST reenviar a mesma mensagem em texto
simples antes de desistir, para nunca perder uma notificação por causa de
formatação. Esse fallback MUST ter teste automatizado dedicado (ver
Princípio X). Qualquer log ou exceção que inclua o corpo de uma resposta ou
requisição MUST sanitizar tokens de bot antes de ser exibido, logado ou
lançado.

### IX. Segredos Somente via GitHub Secrets
Tokens dos bots do Telegram, seus respectivos chat_ids, e qualquer chave de
API adicional (ex.: Anthropic) MUST ser fornecidos exclusivamente via
GitHub Secrets injetados como variáveis de ambiente no workflow do GitHub
Actions. É PROIBIDO commitar segredos em texto plano no código, em
arquivos de configuração versionados, em logs de execução ou em mensagens
de erro. O e-mail/identidade de autor usada em commits automatizados
(workflow) MUST ser uma identidade de bot (`github-actions[bot]` ou
equivalente), nunca uma identidade pessoal.

### X. Portão de CI Automatizado
Nenhum código MUST chegar a `main` sem que a suíte de testes automatizados
tenha rodado com sucesso — via workflow de CI dedicado (`ci.yml`),
disparado em todo pull request, independente do workflow de produção
(`monitor.yml`). É PROIBIDO depender de execução manual de testes como
único gate antes de um merge. Toda função crítica para a garantia de
idempotência (Princípio V) e de resiliência de notificação (Princípio
VIII) — incluindo o fallback de formatação do Telegram e a função de
alerta de falha (`notificar_falha`) — MUST ter teste automatizado dedicado,
não apenas cobertura indireta via outros testes.

## Architecture Constraints

- **Linguagem e runtime**: Python 3.12.
- **Execução**: GitHub Actions agendado via cron; sem servidor dedicado,
  sem custo além do tier gratuito de cada serviço usado (GitHub Actions,
  APIs públicas do BCB/IBGE, Telegram Bot API).
- **Armazenamento**: arquivos JSON (`estado.json`) e Markdown/JSON de
  histórico no próprio repositório Git — sem banco de dados externo.
- **Observabilidade mínima**: um workflow separado de watchdog diário
  (`watchdog.yml`) consulta a API de execuções do próprio GitHub Actions e
  alerta se o cron principal (`monitor.yml`) parou de rodar ou falhou
  repetidamente. Esse watchdog MUST NUNCA disparar um alerta falso quando a
  lista de execuções estiver vazia (cold start de um workflow recém-criado).
- **CI independente de produção**: o workflow de CI (`ci.yml`, Princípio X)
  MUST permanecer separado do workflow de produção (`monitor.yml`) — nunca
  compartilhar o mesmo arquivo, para que uma falha de teste não seja
  confundida com uma falha de execução em produção, nem vice-versa.
- **Reaproveitamento de padrões do projeto irmão**: a assinatura de
  `enviar_mensagem(texto, token, chat_id)` do copom-monitor-pm MUST ser
  reaproveitada como está (parametrizada por token/chat_id). Funções de
  retry (`_retentavel`, `_espera_para_tentativa`), sanitização
  (`_sanitizar`) e isolamento de execução (`_executar_isolado`) do projeto
  irmão MUST ser reaproveitadas ou adaptadas em vez de reimplementadas do
  zero.

## Development Workflow

- Cada fluxo novo MUST ser especificado, planejado e implementado como uma
  feature independente do Spec Kit (`specs/<NNN>-<nome-do-fluxo>/`), ainda
  que compartilhe infraestrutura comum (retry HTTP, envio ao Telegram,
  isolamento de execução) — trilha completa do Princípio I.
- A primeira tarefa técnica de cada fluxo novo, ou de qualquer integração
  com uma API externa nova, MUST ser a verificação do contrato real
  (Princípio II), bloqueando as tarefas seguintes daquele fluxo até que o
  payload real seja fornecido pelo usuário.
- Ajustes feitos pela trilha leve (Princípio I) NÃO exigem `tasks.md`, mas
  MUST deixar rastro em `research.md`/changelog da feature afetada e citar
  o `specs/NNN-*` correspondente no commit/PR.
- Todo PR MUST passar pelo gate de CI (Princípio X) antes de ser mergeado.
- Revisões de código e de spec MUST verificar conformidade com os dez
  princípios acima antes de aprovar merge de qualquer PR.
- **Sincronização periódica de documentação**: a cada bloco relevante de
  mudanças pela trilha leve (recomendado: a cada 5–10 PRs, ou quando
  solicitado), MUST ser feita uma varredura ativa comparando `specs/*`, a
  constituição e o código real, corrigindo divergências encontradas — não
  esperar uma auditoria ser pedida explicitamente para isso acontecer.

## Governance

Esta constituição tem precedência sobre qualquer outra prática, convenção
de código ou preferência individual dentro deste repositório. Qualquer
conflito entre esta constituição e um documento de plano, spec ou tarefa
MUST ser resolvido a favor da constituição, com o documento conflitante
corrigido. Quando a prática real (uma decisão de produto já em produção)
diverge do texto da constituição, a divergência MUST ser resolvida por
emenda formal — nunca deixada acumulando silenciosamente nem "corrigida"
só no código sem atualizar o texto.

**Emendas**: alterações a esta constituição MUST ser feitas exclusivamente
via `/speckit-constitution`, produzindo um novo Sync Impact Report e
incrementando a versão conforme versionamento semântico:
- **MAJOR**: remoção ou redefinição incompatível de um princípio existente.
- **MINOR**: adição de um novo princípio ou expansão material de uma
  seção existente.
- **PATCH**: esclarecimentos de redação, correções de digitação, ajustes
  não semânticos.
Emendar a constituição MUST ser tratado como parte normal do fluxo de
trabalho sempre que uma decisão de arquitetura em produção contradizer um
princípio existente — não como um evento raro reservado a mudanças
grandes.

**Conformidade**: todo `/speckit-plan` MUST incluir uma verificação
explícita ("Constitution Check") de que o plano proposto não viola nenhum
dos dez princípios, especialmente os Princípios II (contrato não
verificado), III (isolamento de fluxos), V (idempotência) e X (portão de
CI), que são as fontes mais prováveis de regressão em produção.

**Version**: 2.0.0 | **Ratified**: 2026-07-03 | **Last Amended**: 2026-07-05
