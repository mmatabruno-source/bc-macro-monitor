# Feature Specification: Alerta de Mudança Relevante no Focus para a Próxima Reunião do Copom

**Feature Branch**: `001-focus-copom-alert`

**Created**: 2026-07-03

**Status**: Draft

**Input**: User description: "Alertar quando houver mudança relevante na expectativa de mercado (Focus) do BCB para a próxima reunião do Copom, notificando via bot dedicado do Telegram"

## Clarifications

### Session 2026-07-03

- Q: Qual estatística do Focus deve ser a fonte de verdade única para
  acompanhar a expectativa da próxima reunião do Copom? → A: Mediana.
- Q: O que conta como "mudança relevante" o suficiente para disparar uma
  notificação? → A: Não há limiar — toda nova divulgação do Focus para a
  próxima reunião gera notificação, com o texto da mensagem comparando a
  divulgação nova contra a anterior (subiu, desceu ou manteve).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ser avisado quando o mercado revisa a expectativa de Selic para a próxima reunião (Priority: P1)

Como acompanhante de política monetária para apoio a decisões de portfólio, quero
receber uma mensagem no Telegram a cada nova divulgação do boletim Focus
para a próxima reunião do Copom, com um comparativo claro (subiu, desceu ou
manteve) em relação à divulgação anterior, para não precisar checar o
boletim Focus manualmente.

**Why this priority**: É o núcleo do fluxo — sem isso não há produto. Cada
nova divulgação do Focus é, por si só, um sinal de portfólio relevante,
mesmo quando o valor se mantém (a manutenção também é informação).

**Independent Test**: Pode ser testado de forma independente simulando duas
divulgações consecutivas da API do Focus (identificadas por datas de
referência distintas) para a próxima reunião e verificando que uma mensagem
é enviada ao bot dedicado deste fluxo a cada divulgação nova, contendo o
valor anterior, o novo valor, a indicação de direção (subiu/desceu/manteve)
e a data da próxima reunião.

**Acceptance Scenarios**:

1. **Given** a última divulgação registrada em `estado.json` para a próxima
   reunião do Copom tinha mediana X, **When** a checagem periódica encontra
   uma nova divulgação (data de referência distinta) com mediana Y, **Then**
   o sistema envia uma notificação ao bot do fluxo Focus contendo o valor
   anterior, o novo valor, a indicação textual de direção (subiu/desceu/
   manteve, incluindo o caso Y = X) e a data/identificação da reunião, e só
   então registra a nova divulgação como a mais recente processada em
   `estado.json`.
2. **Given** a última divulgação registrada já foi processada e notificada
   com sucesso, **When** a checagem periódica roda novamente e a API ainda
   reporta a mesma divulgação (mesma data de referência), **Then** o sistema
   não envia nenhuma notificação nova e não altera `estado.json`
   (idempotência por divulgação, não apenas por valor).

---

### User Story 2 - Continuar recebendo alertas após a reunião do Copom acontecer (Priority: P2)

Como usuário do monitor, quero que o fluxo identifique automaticamente qual é
a "próxima reunião" à medida que reuniões passam, para não precisar
reconfigurar manualmente qual data o sistema deve observar.

**Why this priority**: Sem esse comportamento, o fluxo pararia de funcionar
corretamente (ou passaria a monitorar uma reunião já ocorrida) poucos meses
após o primeiro deploy, tornando o produto de vida curta sem intervenção
manual.

**Independent Test**: Pode ser testado simulando a passagem da data de uma
reunião (a reunião que era "próxima" se torna passada) e verificando que o
sistema passa a monitorar a expectativa da reunião seguinte, sem baseline
anterior para essa nova reunião (ou seja, sem gerar uma notificação com
comparação "subiu/desceu/manteve" espúria apenas por trocar de reunião de
referência — a primeira divulgação da nova reunião é registrada como
baseline informativa, sem comparação numérica contra a reunião anterior).

**Acceptance Scenarios**:

1. **Given** a reunião anteriormente monitorada como "próxima" já ocorreu,
   **When** a checagem periódica roda, **Then** o sistema identifica a nova
   próxima reunião a partir da API oficial (nunca de um calendário fixo
   hardcoded) e passa a monitorar a expectativa de mercado para ela.
2. **Given** a troca de reunião monitorada descrita acima, **When** a
   expectativa da nova reunião é lida pela primeira vez, **Then** o sistema
   envia uma notificação informando o valor inicial da mediana Focus para a
   nova reunião, sem indicação de direção (subiu/desceu/manteve), já que não
   há divulgação anterior da mesma reunião para comparar, e registra esse
   valor em `estado.json` como referência para futuras comparações.

---

### User Story 3 - Ser avisado imediatamente se o fluxo parar de funcionar (Priority: P3)

Como usuário do monitor, quero ser avisado no mesmo bot do fluxo Focus se uma
checagem falhar de forma inesperada (ex.: API fora do ar, formato de resposta
mudou), para saber que preciso investigar em vez de assumir silenciosamente
que "não houve mudança".

**Why this priority**: Aumenta a confiança no sistema, mas o fluxo já entrega
valor (User Story 1) mesmo sem esse aviso — é uma camada de robustez, não o
núcleo do produto.

**Independent Test**: Pode ser testado forçando uma exceção durante a
checagem (ex.: resposta HTTP malformada) e verificando que uma mensagem de
falha é enviada ao bot do fluxo Focus, que a execução dos outros dois fluxos
(Relatório de Política Monetária, IPCA) não é afetada, e que nenhuma
alteração é feita em `estado.json` para o fluxo Focus.

**Acceptance Scenarios**:

1. **Given** a API do Focus está indisponível ou retorna um formato
   inesperado durante uma checagem, **When** a execução agendada roda,
   **Then** o sistema captura o erro, envia um aviso de falha ao bot do
   fluxo Focus, não modifica `estado.json` para este fluxo, e permite que os
   outros dois fluxos executem normalmente na mesma execução.

---

### Edge Cases

- O que acontece se a API do Focus retornar múltiplas reuniões futuras na
  mesma resposta? O sistema deve identificar de forma inequívoca qual é "a
  próxima reunião do Copom" entre elas (a mais próxima cronologicamente com
  data futura).
- O que acontece na primeíssima execução do fluxo, quando `estado.json` ainda
  não tem nenhuma expectativa registrada para nenhuma reunião? O sistema
  envia uma notificação informativa de valor inicial, sem indicação de
  direção (mesmo comportamento do FR-008/cenário 2 da User Story 2 — não há
  "subiu/desceu/manteve" sem uma divulgação anterior para comparar).
- O que acontece se a mesma divulgação for lida em duas execuções agendadas
  consecutivas antes de uma nova divulgação existir (ex.: checagem diária
  contra publicação semanal)? Como a idempotência é por data de referência
  da divulgação (FR-004a/FR-007), nenhuma notificação repetida é enviada
  entre essas execuções — a próxima notificação só ocorre quando a API
  reportar uma divulgação com data de referência nova.
- O que acontece se a API retornar simultaneamente mais de uma estatística
  para a mesma divulgação (mediana, média, etc.)? Fora de escopo de
  ambiguidade — a mediana é a única estatística usada por este fluxo
  (FR-011); as demais são ignoradas.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST checar periodicamente (via execução agendada) a
  expectativa de mercado (Focus) publicada pelo Banco Central para a taxa
  Selic na próxima reunião do Copom.
- **FR-002**: O sistema MUST determinar qual é "a próxima reunião do Copom"
  a partir da própria API oficial consultada (nunca de uma lista de datas
  fixa mantida manualmente no repositório).
- **FR-003**: O sistema MUST comparar o valor de expectativa observado na
  checagem atual com o último valor registrado em `estado.json` para a
  mesma reunião.
- **FR-004**: O sistema MUST tratar toda nova divulgação do boletim Focus
  para a próxima reunião do Copom como digna de notificação — não existe um
  limiar mínimo de variação; mesmo que o valor da estatística acompanhada
  não tenha mudado desde a última divulgação processada, uma nova
  divulgação ainda gera notificação (ver FR-004a).
- **FR-004a**: O sistema MUST identificar de forma inequívoca cada
  "divulgação" do Focus (ex.: pela data de referência da pesquisa retornada
  pela API), de modo a distinguir "uma nova divulgação com o mesmo valor de
  antes" de "a mesma divulgação já processada" — apenas a primeira gera
  notificação; a segunda é ignorada por idempotência (ver FR-007).
- **FR-005**: O sistema MUST enviar, a cada nova divulgação processada, uma
  notificação ao bot do Telegram dedicado a este fluxo, contendo pelo menos:
  o valor anterior, o novo valor, a identificação da reunião do Copom a que
  a expectativa se refere, e uma indicação textual explícita da direção da
  mudança (subiu, desceu ou manteve em relação à divulgação anterior
  processada).
- **FR-006**: O sistema MUST registrar a nova divulgação (valor e data de
  referência) em `estado.json` como a expectativa mais recente processada
  SOMENTE depois que o envio da notificação for confirmado como
  bem-sucedido.
- **FR-007**: O sistema MUST NOT enviar uma segunda notificação para uma
  divulgação já notificada e registrada com sucesso (idempotência baseada na
  data de referência da divulgação, não apenas no valor).
- **FR-008**: O sistema MUST tratar a primeira divulgação processada para uma
  nova reunião (sem baseline anterior em `estado.json` para essa reunião)
  como uma notificação informativa de valor inicial, sem indicação de
  direção (subiu/desceu/manteve), já que não existe divulgação anterior da
  mesma reunião para comparar; o valor é registrado como referência para as
  próximas divulgações dessa reunião.
- **FR-009**: O sistema MUST isolar falhas deste fluxo de forma que uma
  exceção inesperada durante a checagem não impeça a execução ou notificação
  dos outros dois fluxos (Relatório de Política Monetária, IPCA) na mesma
  execução agendada.
- **FR-010**: O sistema MUST notificar falhas inesperadas deste fluxo
  especificamente ao bot dedicado ao fluxo Focus, nunca a um bot de outro
  fluxo.
- **FR-011**: O sistema MUST usar a mediana das expectativas de mercado para
  a Selic na próxima reunião do Copom como a estatística única e fonte de
  verdade para a comparação "subiu/desceu/manteve" e para o valor reportado
  na notificação (dentre as estatísticas tipicamente publicadas no Focus —
  mediana, média, desvio-padrão, mínimo, máximo, número de respondentes —,
  a mediana é o padrão de mercado adotado por este fluxo).

### Key Entities *(include if feature involves data)*

- **Divulgação Focus da Próxima Reunião**: representa uma publicação
  específica (identificada por sua data de referência) da mediana das
  expectativas de mercado para a Selic na próxima reunião do Copom. É a
  unidade que o sistema compara a cada checagem para decidir se há uma nova
  divulgação a notificar.
- **Registro de Estado do Fluxo Focus**: a chave `ultima_expectativa_copom`
  em `estado.json`, contendo a última divulgação processada (mediana e data
  de referência) e a reunião a que ela se refere, usada para garantir
  idempotência por divulgação e para detectar troca de reunião de
  referência.
- **Notificação de Divulgação**: mensagem enviada ao bot dedicado do fluxo
  Focus a cada nova divulgação processada, contendo valor anterior (quando
  existir), novo valor, indicação de direção (subiu/desceu/manteve, quando
  aplicável) e identificação da reunião.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Toda nova divulgação do boletim Focus para a próxima reunião
  do Copom gera exatamente uma notificação no bot dedicado, dentro do
  intervalo de uma execução agendada (nunca mais de uma execução de atraso)
  após a divulgação ser publicada pelo Banco Central.
- **SC-002**: Zero notificações duplicadas são enviadas para a mesma
  divulgação já processada, mesmo que o sistema rode centenas de execuções
  agendadas consecutivas sem uma nova divulgação publicada.
- **SC-003**: Zero notificações com comparação "subiu/desceu/manteve"
  espúria são geradas unicamente por causa da troca da reunião monitorada de
  uma reunião já ocorrida para a próxima (a primeira divulgação da nova
  reunião é sempre informativa, sem comparação).
- **SC-004**: Uma falha inesperada neste fluxo nunca impede que os outros
  dois fluxos monitorados pelo mesmo sistema completem sua checagem e
  notificação na mesma execução.

## Assumptions

- O boletim Focus é publicado com frequência regular (tipicamente semanal)
  pelo Banco Central, e uma execução agendada diária é suficiente para
  capturar mudanças sem atraso relevante para decisões de portfólio.
- Existe um bot do Telegram dedicado a este fluxo (token e chat_id próprios),
  a ser criado e configurado como GitHub Secret antes do primeiro deploy —
  fora do escopo desta spec, que trata apenas do comportamento do fluxo.
- "Próxima reunião do Copom" é sempre identificável de forma inequívoca a
  partir da resposta da API oficial (existe sempre uma reunião futura mais
  próxima cronologicamente).
- O formato exato do payload da API de expectativas (Focus) ainda não foi
  verificado por uma chamada de teste real — por princípio deste projeto,
  nenhum cliente HTTP ou parser será escrito até que o usuário forneça a
  resposta real de uma chamada de teste; esta spec descreve apenas o
  comportamento esperado, não a estrutura de dados da API.
