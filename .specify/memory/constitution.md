<!--
Sync Impact Report
Version change: N/A (template) → 1.0.0
Modified principles: none (initial ratification)
Added sections:
  - Core Principles I–IX
  - Architecture Constraints
  - Development Workflow
  - Governance
Removed sections: none
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ (generic Constitution Check gate references this file, no changes needed)
  - .specify/templates/spec-template.md ✅ (no constitution-specific placeholders to sync)
  - .specify/templates/tasks-template.md ✅ (task categorization already generic; per-flow task grouping to be applied in each feature's tasks.md)
  - .specify/templates/commands/*.md ⚠ pending (agent-generic references only; no action required at this time)
  - README.md ⚠ pending (should be expanded with project overview once first flow ships)
Follow-up TODOs: none
-->

# bc-macro-monitor Constitution

## Core Principles

### I. Spec-Driven Development, Sem Exceções (NON-NEGOTIABLE)
Toda mudança de código, por menor que pareça — incluindo ajustes triviais, correções
de digitação em mensagens, ou mudanças de configuração — MUST passar pelo fluxo
completo do GitHub Spec Kit, nesta ordem: `/speckit-constitution` →
`/speckit-specify` → `/speckit-plan` → `/speckit-tasks` → `/speckit-implement`.
É PROIBIDO pular etapas ou escrever código de aplicação diretamente sem uma
spec, um plano e uma lista de tarefas aprovados. Cada commit de implementação
MUST referenciar o ID da tarefa de `tasks.md` que ele resolve (ex.:
`T014: implementar parser da série 433 do SGS`). Qualquer ambiguidade
encontrada na especificação MUST ser resolvida via `/speckit-clarify`,
perguntando ao usuário — nunca preenchida por suposição do agente.
**Racional**: o processo já provou reduzir retrabalho no projeto irmão
copom-monitor-pm; pular etapas é exatamente o que causou o contrato de API
incorreto que motivou o Princípio II abaixo.

### II. Nunca Codificar Contra um Contrato de API Não Verificado (NON-NEGOTIABLE)
Para CADA endpoint externo novo que qualquer fluxo deste projeto vier a
consumir — incluindo, mas não limitado a, os três candidatos iniciais
(`ExpectativasMercadoSelic`/Focus, dataset de Relatórios de Política
Monetária, série 433 do SGS/IPCA) — é PROIBIDO escrever qualquer cliente
HTTP, parser ou modelo de dados antes de o usuário colar a resposta JSON
real de uma chamada de teste executada de fato (navegador, curl ou
Postman). O arquivo `contracts/*.md` correspondente só pode ser escrito a
partir do payload real observado. Documentação de terceiros, exemplos de
blog ou "formato razoável esperado" NUNCA são fonte válida para o contrato.
Se o payload real ainda não foi fornecido, a tarefa correspondente MUST
ficar bloqueada e o agente MUST parar e pedir explicitamente ao usuário
que cole a resposta de teste antes de prosseguir.
**Racional**: no projeto irmão, o primeiro contrato para a API de
Comunicados do BCB foi escrito com base numa hipótese não verificada e
teve que ser reescrito após testar no navegador — o custo de verificar
antes é sempre menor que o custo de descobrir depois, em produção.

### III. Isolamento Total Entre os Três Fluxos
Os três fluxos (Focus/Copom, Relatório de Política Monetária, IPCA) MUST
ser tratados como unidades de falha independentes dentro da mesma execução
agendada. Uma exceção não tratada em um fluxo MUST ser capturada, logada e
notificada ao bot daquele fluxo especificamente, e MUST NUNCA impedir a
checagem, o processamento ou a notificação dos outros dois fluxos na mesma
execução. Cada fluxo tem sua própria chave de estado em `estado.json`
(`ultima_expectativa_copom`, `ultimo_relatorio`, `ultimo_ipca`) e seu
próprio diretório de histórico (`historico/focus/`, `historico/relatorios/`,
`historico/ipca/`), para que uma corrupção ou erro de leitura em um não
contamine os demais.

### IV. Notificação por Bot Dedicado, Sem Bot Padrão
Cada fluxo publica em um bot/chat do Telegram próprio (token e chat_id
independentes, via GitHub Secrets). Não existe um bot "padrão" ou de
fallback compartilhado entre fluxos, ao contrário do projeto irmão
(que tem um único bot). Toda função de notificação — inclusive
`notificar_falha` — MUST receber explicitamente qual bot/chat pertence ao
fluxo que está reportando, e MUST NUNCA enviar o aviso de falha de um
fluxo para o bot de outro.

### V. Idempotência de Publicação
Nenhuma publicação já processada MUST gerar uma segunda notificação. O
registro de "processado" em `estado.json` só MUST ser gravado DEPOIS que o
envio ao Telegram for confirmado como bem-sucedido (HTTP 2xx). Se a
notificação falhar, o estado MUST permanecer como "não processado" para
que a próxima execução tente novamente — falhar ao notificar nunca pode
ser confundido com falhar ao processar.

### VI. API Oficial como Única Fonte de Verdade
A fonte de verdade de cada fluxo MUST ser sempre a API oficial
correspondente (Olinda/Expectativas de Mercado, dataset de Relatórios de
Política Monetária, SGS série 433), nunca um calendário de datas estimadas
de publicação. Um calendário MAY ser usado para ajustar a frequência de
checagem (ex.: checar o IPCA com mais frequência perto do dia esperado de
divulgação), mas MUST NUNCA ser usado para decidir se um fluxo verifica ou
deixa de verificar a API naquela execução.

### VII. Simplicidade Sobre Otimização Prematura
Entre duas soluções corretas, a mais simples MUST vencer. É PROIBIDO
introduzir filas, workers, bancos de dados externos ou frameworks
adicionais além do necessário para os três fluxos descritos. Armazenamento
MUST permanecer em arquivos JSON e Markdown versionados no próprio
repositório Git. Abstrações genéricas antecipando fluxos futuros
hipotéticos MUST ser evitadas — construir para os três fluxos existentes,
não para "fluxos futuros".

### VIII. Resiliência de Rede e de Notificação
Toda chamada HTTP externa MUST usar retry seletivo: retentar em 429
(respeitando o header `Retry-After` quando presente) e em 5xx
(indisponibilidade transitória), e MUST NUNCA retentar em outros códigos
4xx (ex.: 404), que são permanentes. Todo envio ao Telegram MUST ter
fallback de formatação — se o Markdown for rejeitado (HTTP 400 com erro de
parsing de entidades), o sistema MUST reenviar a mesma mensagem em texto
simples antes de desistir, para nunca perder uma notificação por causa de
formatação. Qualquer log ou exceção que inclua o corpo de uma resposta ou
requisição MUST sanitizar tokens de bot antes de ser exibido, logado ou
lançado.

### IX. Segredos Somente via GitHub Secrets
Tokens dos três bots do Telegram, seus respectivos chat_ids, e qualquer
chave de API adicional (ex.: Anthropic, se usada) MUST ser fornecidos
exclusivamente via GitHub Secrets injetados como variáveis de ambiente no
workflow do GitHub Actions. É PROIBIDO commitar segredos em texto plano no
código, em arquivos de configuração versionados, em logs de execução ou em
mensagens de erro.

## Architecture Constraints

- **Linguagem e runtime**: Python 3.12.
- **Execução**: GitHub Actions agendado via cron; sem servidor dedicado,
  sem custo além do tier gratuito de cada serviço usado (GitHub Actions,
  APIs públicas do BCB, Telegram Bot API).
- **Armazenamento**: arquivos JSON (`estado.json`) e Markdown/JSON de
  histórico no próprio repositório Git — sem banco de dados externo.
- **Observabilidade mínima**: um workflow separado de watchdog diário
  MUST consultar a API de execuções do próprio GitHub Actions e alertar se
  o cron principal parou de rodar ou falhou repetidamente. Esse watchdog
  MUST NUNCA disparar um alerta falso quando a lista de execuções estiver
  vazia (cold start de um workflow recém-criado).
- **Reaproveitamento de padrões do projeto irmão**: a assinatura de
  `enviar_mensagem(texto, token, chat_id)` do copom-monitor-pm MUST ser
  reaproveitada como está (parametrizada por token/chat_id) para suportar
  os três bots deste projeto — um por fluxo. Funções de retry
  (`_retentavel`, `_espera_para_tentativa`), sanitização (`_sanitizar`) e
  isolamento de execução (`_executar_isolado`) do projeto irmão MUST ser
  reaproveitadas ou adaptadas em vez de reimplementadas do zero.

## Development Workflow

- Cada fluxo (Focus, Relatório de Política Monetária, IPCA) MUST ser
  especificado, planejado e implementado como uma feature independente do
  Spec Kit (`specs/<NNN>-<nome-do-fluxo>/`), ainda que compartilhem
  infraestrutura comum (retry HTTP, envio ao Telegram, isolamento de
  execução).
- A primeira tarefa técnica de cada fluxo MUST ser a verificação do
  contrato real da API correspondente (Princípio II), bloqueando as
  tarefas seguintes daquele fluxo até que o payload real seja fornecido
  pelo usuário.
- Cada tarefa de `tasks.md` MUST resultar em exatamente um commit,
  referenciando o ID da tarefa na mensagem de commit.
- Revisões de código e de spec MUST verificar conformidade com os nove
  princípios acima antes de aprovar merge de qualquer PR.

## Governance

Esta constituição tem precedência sobre qualquer outra prática, convenção
de código ou preferência individual dentro deste repositório. Qualquer
conflito entre esta constituição e um documento de plano, spec ou tarefa
MUST ser resolvido a favor da constituição, com o documento conflitante
corrigido.

**Emendas**: alterações a esta constituição MUST ser feitas exclusivamente
via `/speckit-constitution`, produzindo um novo Sync Impact Report e
incrementando a versão conforme versionamento semântico:
- **MAJOR**: remoção ou redefinição incompatível de um princípio existente.
- **MINOR**: adição de um novo princípio ou expansão material de uma
  seção existente.
- **PATCH**: esclarecimentos de redação, correções de digitação, ajustes
  não semânticos.

**Conformidade**: todo `/speckit-plan` MUST incluir uma verificação
explícita ("Constitution Check") de que o plano proposto não viola nenhum
dos nove princípios, especialmente os Princípios II (contrato não
verificado), III (isolamento de fluxos) e V (idempotência), que são as
fontes mais prováveis de regressão em produção.

**Version**: 1.0.0 | **Ratified**: 2026-07-03 | **Last Amended**: 2026-07-03
