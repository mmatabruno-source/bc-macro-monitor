# Feature Specification: Notificação da Publicação do Relatório de Política Monetária

**Feature Branch**: `002-relatorio-politica-monetaria`

**Created**: 2026-07-03

**Status**: Draft

**Input**: User description: "Notificar a publicação do Relatório de Política Monetária trimestral do BCB, com análise crítica orientada a decisão de portfólio em várias mensagens sequenciais no Telegram, nos mesmos moldes da análise de Ata já validada no copom-monitor-pm"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ser avisado assim que um novo Relatório de Política Monetária é publicado (Priority: P1)

Como acompanhante de política monetária para apoio a decisões de portfólio,
quero ser avisado no Telegram assim que o Banco Central publicar um novo
Relatório de Política Monetária (trimestral), para não depender de checar o
site do BCB manualmente a cada trimestre.

**Why this priority**: É o núcleo do fluxo — sem detecção de publicação não
há produto. O Relatório é um evento raro (4x/ano) mas de alto valor
informativo: contém as projeções oficiais de inflação e o cenário macro que
fundamentam as decisões futuras do Copom.

**Independent Test**: Pode ser testado simulando duas checagens consecutivas
do dataset de relatórios publicados, uma sem o novo relatório e outra com
ele, verificando que uma notificação é enviada ao bot dedicado deste fluxo
somente quando o novo relatório aparece, e que o relatório é registrado em
`estado.json` somente após a notificação ser confirmada como enviada.

**Acceptance Scenarios**:

1. **Given** o último relatório registrado em `estado.json` é o do
   trimestre anterior, **When** a checagem periódica encontra um relatório
   novo (referente a um trimestre ainda não processado) no dataset oficial,
   **Then** o sistema envia a sequência de notificações ao bot do fluxo
   Relatório e só então registra o novo relatório como processado.
2. **Given** o último relatório registrado já é o mais recente disponível
   no dataset, **When** a checagem periódica roda novamente, **Then**
   nenhuma notificação é enviada e `estado.json` não é alterado
   (idempotência).

---

### User Story 2 - Receber uma leitura crítica orientada a portfólio, não só o aviso de publicação (Priority: P2)

Como usuário do monitor, quero que a notificação vá além de "saiu um
relatório novo" — quero uma leitura estruturada do cenário macro, das
projeções oficiais de inflação, e do que isso muda para o posicionamento de
portfólio, em mensagens sequenciais, no mesmo espírito da análise de Ata já
validada no copom-monitor-pm.

**Why this priority**: Aumenta muito o valor do fluxo em relação a um
simples "saiu o relatório", mas o fluxo já entrega valor mínimo sem isso
(User Story 1) — por isso é P2, não P1.

**Independent Test**: Pode ser testado fornecendo o conteúdo de um relatório
de teste (real ou fixture) ao gerador de análise e verificando que a
sequência de mensagens enviada cobre, no mínimo: cenário macro, projeções
oficiais de inflação, e implicação para portfólio, em mensagens distintas e
na mesma ordem a cada execução.

**Acceptance Scenarios**:

1. **Given** um novo relatório foi detectado (User Story 1), **When** o
   sistema monta a notificação, **Then** ele envia uma sequência de
   mensagens ao bot do fluxo Relatório cobrindo, nesta ordem: (a) aviso de
   publicação com link ao documento oficial, (b) cenário macro descrito no
   relatório, (c) projeções oficiais de inflação, (d) leitura de implicação
   para decisões de portfólio.
2. **Given** a análise depende de conteúdo do relatório que não pôde ser
   obtido ou interpretado (ex.: formato inesperado), **When** o sistema
   tenta montar as mensagens (b)–(d), **Then** ele ainda envia a mensagem
   (a) (aviso de publicação com link), e trata a falha de análise como
   falha isolada deste fluxo (ver User Story 3), sem deixar de informar ao
   menos que o relatório foi publicado.

---

### User Story 3 - Ser avisado se o fluxo parar de funcionar (Priority: P3)

Como usuário do monitor, quero ser avisado no bot do fluxo Relatório se uma
checagem falhar de forma inesperada, para saber que preciso investigar.

**Why this priority**: Camada de robustez, consistente com os outros dois
fluxos do repositório — não é o núcleo do produto, mas aumenta a confiança
no sistema.

**Independent Test**: Forçar uma exceção durante a checagem (ex.: dataset
indisponível) e verificar que uma notificação de falha é enviada ao bot do
fluxo Relatório, que os outros dois fluxos do repositório não são afetados,
e que `estado.json` não é alterado para este fluxo.

**Acceptance Scenarios**:

1. **Given** o dataset de relatórios está indisponível ou retorna um
   formato inesperado durante uma checagem, **When** a execução agendada
   roda, **Then** o sistema captura o erro, envia um aviso de falha ao bot
   do fluxo Relatório, não modifica `estado.json` para este fluxo, e
   permite que os outros dois fluxos executem normalmente na mesma
   execução.

---

### Edge Cases

- O que acontece se dois relatórios forem publicados no mesmo trimestre
  (ex.: correção/republicação)? O sistema deve tratar como o mesmo
  relatório já processado se referirem-se ao mesmo período, ou como um novo
  se o dataset expuser um identificador de versão distinto — a
  identificação exata do "identificador de relatório" depende do contrato
  real do dataset (ver Assumptions).
- O que acontece na primeiríssima execução do fluxo, sem nenhum relatório
  registrado em `estado.json`? O relatório mais recente disponível no
  dataset é registrado como baseline processado, com notificação enviada
  normalmente (diferente do fluxo Focus, aqui não há conceito de "sem
  comparação direcional" — cada relatório é um evento discreto, não uma
  série contínua a comparar).
- O que acontece se o conteúdo necessário para a análise crítica (User
  Story 2) só estiver disponível em PDF, sem texto estruturado via API? Ver
  Assumptions — esta é uma decisão técnica que depende do payload real do
  dataset e será resolvida via `/speckit-clarify` na fase de planejamento,
  não assumida aqui.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST checar periodicamente (execução agendada
  diária) o dataset oficial de Relatórios de Política Monetária publicados
  pelo Banco Central.
- **FR-002**: O sistema MUST identificar um relatório como "novo" quando
  ele se referir a um período/trimestre ainda não registrado como
  processado em `estado.json`.
- **FR-003**: O sistema MUST enviar, ao detectar um relatório novo, uma
  sequência de notificações ao bot do Telegram dedicado a este fluxo,
  cobrindo no mínimo: aviso de publicação com link ao documento oficial,
  cenário macro, projeções oficiais de inflação, e implicação para
  portfólio.
- **FR-004**: O sistema MUST registrar o novo relatório como processado em
  `estado.json` SOMENTE depois que a sequência de notificações for
  confirmada como enviada com sucesso.
- **FR-005**: O sistema MUST NOT enviar uma segunda notificação para um
  relatório já registrado como processado (idempotência).
- **FR-006**: O sistema MUST enviar ao menos o aviso de publicação (com
  link ao documento) mesmo se as mensagens de análise crítica (cenário
  macro, projeções, portfólio) não puderem ser montadas por falha na
  obtenção ou interpretação do conteúdo do relatório.
- **FR-007**: O sistema MUST isolar falhas deste fluxo de forma que uma
  exceção inesperada durante a checagem não impeça a execução ou
  notificação dos outros dois fluxos (Focus, IPCA) na mesma execução
  agendada.
- **FR-008**: O sistema MUST notificar falhas inesperadas deste fluxo
  especificamente ao bot dedicado ao fluxo Relatório, nunca a um bot de
  outro fluxo.
- **FR-009**: O sistema MUST usar o dataset oficial de relatórios como
  única fonte de verdade para decidir se um relatório novo foi publicado,
  nunca um calendário estimado de datas de publicação (calendário trimestral
  pode, no máximo, informar que a checagem pode ser feita com frequência
  reduzida, nunca decidir se a checagem ocorre).

### Key Entities *(include if feature involves data)*

- **Relatório de Política Monetária**: representa uma publicação trimestral
  específica, identificada por período/trimestre de referência, contendo
  (conforme o contrato real a ser verificado) metadados como data de
  publicação e link para o documento, e possivelmente conteúdo estruturado
  ou apenas um PDF.
- **Registro de Estado do Fluxo Relatório**: a chave `ultimo_relatorio` em
  `estado.json`, contendo o identificador do último relatório processado
  com sucesso.
- **Análise Crítica de Portfólio**: conjunto de mensagens sequenciais
  geradas a partir do conteúdo do relatório, cobrindo cenário macro,
  projeções oficiais de inflação e implicação para portfólio — o mecanismo
  exato de geração (ex.: uso de LLM) é um detalhe técnico a definir na fase
  de planejamento, não nesta spec.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Todo novo Relatório de Política Monetária publicado gera
  exatamente uma sequência de notificações no bot dedicado, dentro do
  intervalo de uma execução agendada (nunca mais de uma execução de atraso)
  após a publicação.
- **SC-002**: Zero notificações duplicadas são enviadas para o mesmo
  relatório já processado, mesmo que o sistema rode centenas de execuções
  agendadas consecutivas sem nova publicação.
- **SC-003**: Mesmo quando a análise crítica não pode ser gerada, 100% das
  publicações detectadas ainda resultam em ao menos o aviso de publicação
  com link ao documento oficial sendo enviado.
- **SC-004**: Uma falha inesperada neste fluxo nunca impede que os outros
  dois fluxos monitorados pelo mesmo sistema completem sua checagem e
  notificação na mesma execução.

## Assumptions

- O dataset `relatorios-de-inflacao-publicados` do Portal de Dados Abertos
  do BCB é atualizado tempestivamente após cada publicação trimestral, e uma
  checagem agendada diária é suficiente para não gerar atraso relevante
  para decisões de portfólio.
- Existe um bot do Telegram dedicado a este fluxo (`RELATORIO_TELEGRAM_BOT_TOKEN`
  / `RELATORIO_TELEGRAM_CHAT_ID`), a ser criado e configurado como GitHub
  Secret antes do primeiro deploy — fora do escopo desta spec.
- O formato exato do payload do dataset (campos, se o conteúdo vem
  estruturado ou apenas como link de PDF) ainda não foi verificado por uma
  chamada de teste real — por princípio deste projeto, nenhum cliente HTTP
  ou parser será escrito até que o usuário forneça a resposta real de uma
  chamada de teste; esta spec descreve apenas o comportamento esperado, não
  a estrutura de dados do dataset.
- Caso o conteúdo do relatório só exista como PDF sem texto estruturado via
  API, a abordagem de extração (ex.: biblioteca de parsing de PDF vs. leitura
  assistida por LLM a partir do link) será decidida via `/speckit-clarify`
  na fase de planejamento, depois que o payload real do dataset for
  conhecido — não é assumida nesta spec.
- O mecanismo de geração da análise crítica (User Story 2) provavelmente
  reaproveita o padrão de análise de Ata já validado no copom-monitor-pm
  (uso de LLM), mas a confirmação de que este projeto usará uma chave de
  API de LLM como novo segredo será revisitada na fase de planejamento.
