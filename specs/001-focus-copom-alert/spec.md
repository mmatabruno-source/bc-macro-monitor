# Feature Specification: Alerta de Mudança Relevante no Focus para a Próxima Reunião do Copom

**Feature Branch**: `001-focus-copom-alert`

**Created**: 2026-07-03

**Status**: Draft

**Input**: User description: "Alertar quando houver mudança relevante na expectativa de mercado (Focus) do BCB para a próxima reunião do Copom, notificando via bot dedicado do Telegram"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ser avisado quando o mercado revisa a expectativa de Selic para a próxima reunião (Priority: P1)

Como acompanhante de política monetária para apoio a decisões de portfólio, quero
receber uma mensagem no Telegram assim que a expectativa de mercado (Focus)
para a taxa Selic na próxima reunião do Copom mudar de forma relevante, para
não precisar checar o boletim Focus manualmente todos os dias.

**Why this priority**: É o núcleo do fluxo — sem isso não há produto. Uma
mudança relevante na expectativa de mercado é um sinal de portfólio tão ou
mais importante que a própria decisão do Copom, porque antecipa a decisão.

**Independent Test**: Pode ser testado de forma independente simulando duas
checagens consecutivas da API do Focus com valores de expectativa
diferentes para a próxima reunião e verificando que uma mensagem é enviada
ao bot dedicado deste fluxo somente na segunda checagem, contendo o valor
anterior, o novo valor e a data da próxima reunião.

**Acceptance Scenarios**:

1. **Given** a última expectativa registrada em `estado.json` para a
   próxima reunião do Copom era X, **When** a checagem periódica encontra um
   novo valor Y na API do Focus tal que a mudança de X para Y é considerada
   relevante, **Then** o sistema envia uma notificação ao bot do fluxo Focus
   contendo o valor anterior, o novo valor e a data/identificação da reunião,
   e só então registra Y como a expectativa mais recente em `estado.json`.
2. **Given** a última expectativa registrada era X, **When** a checagem
   periódica encontra o mesmo valor X (sem mudança), **Then** o sistema não
   envia nenhuma notificação e não altera `estado.json`.
3. **Given** uma notificação já foi enviada com sucesso para uma mudança de
   X para Y, **When** a próxima execução agendada roda e a API ainda reporta
   Y, **Then** nenhuma notificação duplicada é enviada (idempotência).

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
sistema passa a monitorar a expectativa da reunião seguinte, comparando o
novo valor observado contra `null`/ausência de baseline anterior para essa
nova reunião (ou seja, sem gerar uma notificação espúria de "mudança" apenas
por trocar de reunião de referência).

**Acceptance Scenarios**:

1. **Given** a reunião anteriormente monitorada como "próxima" já ocorreu,
   **When** a checagem periódica roda, **Then** o sistema identifica a nova
   próxima reunião a partir da API oficial (nunca de um calendário fixo
   hardcoded) e passa a monitorar a expectativa de mercado para ela.
2. **Given** a troca de reunião monitorada descrita acima, **When** a
   expectativa da nova reunião é lida pela primeira vez, **Then** o sistema
   NÃO envia uma notificação de "mudança" nesse instante (não há baseline
   anterior comparável para essa reunião), apenas registra o valor inicial
   em `estado.json` como referência para futuras comparações.

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
  não tem nenhuma expectativa registrada para nenhuma reunião? O sistema deve
  registrar o valor observado como baseline inicial sem notificar (mesmo
  comportamento do cenário 2 da User Story 2 — não há "mudança" sem um valor
  anterior para comparar).
- O que acontece se a expectativa mudar e depois voltar exatamente ao valor
  anterior antes da próxima checagem (variação dentro da mesma janela)? Como
  o sistema só compara o último valor registrado com o valor mais recente
  observado, essa oscilação intermediária não é vista nem notificada — apenas
  o valor no momento da checagem importa.
- O que acontece se dois ou mais provedores de estatística (ex.: mediana vs.
  média) divergirem sobre a direção da mudança? Fora de escopo — ver Q2
  abaixo sobre qual estatística é a fonte de verdade única deste fluxo.

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
- **FR-004**: O sistema MUST considerar uma mudança "relevante" — e portanto
  digna de notificação — de acordo com o critério definido em [NEEDS
  CLARIFICATION: qual é o limiar/critério de "mudança relevante"? Ex.:
  qualquer mudança de valor (por menor que seja), uma variação mínima em
  pontos percentuais (ex. ≥ 0,25 p.p.), ou uma mudança de "cenário" (ex.:
  mediana passa a apontar para uma decisão de corte/alta/manutenção
  diferente da anterior)?].
- **FR-005**: O sistema MUST enviar, quando uma mudança relevante for
  detectada, uma notificação ao bot do Telegram dedicado a este fluxo,
  contendo pelo menos: o valor anterior, o novo valor, e a identificação da
  reunião do Copom a que a expectativa se refere.
- **FR-006**: O sistema MUST registrar o novo valor em `estado.json` como a
  expectativa mais recente processada SOMENTE depois que o envio da
  notificação for confirmado como bem-sucedido.
- **FR-007**: O sistema MUST NOT enviar uma segunda notificação para uma
  mudança já notificada e registrada com sucesso (idempotência).
- **FR-008**: O sistema MUST NOT tratar a primeira leitura de uma nova
  reunião (sem baseline anterior em `estado.json`) como uma "mudança" —
  apenas registra o valor inicial como referência.
- **FR-009**: O sistema MUST isolar falhas deste fluxo de forma que uma
  exceção inesperada durante a checagem não impeça a execução ou notificação
  dos outros dois fluxos (Relatório de Política Monetária, IPCA) na mesma
  execução agendada.
- **FR-010**: O sistema MUST notificar falhas inesperadas deste fluxo
  especificamente ao bot dedicado ao fluxo Focus, nunca a um bot de outro
  fluxo.
- **FR-011**: O sistema MUST basear a comparação de "mudança" na estatística
  de expectativa definida em [NEEDS CLARIFICATION: entre as estatísticas
  tipicamente publicadas no Focus (mediana, média, desvio-padrão, mínimo,
  máximo, número de respondentes), qual é a estatística única usada como
  fonte de verdade para decidir se houve mudança relevante? Assume-se
  mediana como padrão de mercado, a confirmar].

### Key Entities *(include if feature involves data)*

- **Expectativa Focus da Próxima Reunião**: representa o valor mais recente
  observado da expectativa de mercado para a Selic na próxima reunião do
  Copom, junto com a identificação/data dessa reunião. É o que o sistema
  compara a cada checagem para decidir se houve mudança relevante.
- **Registro de Estado do Fluxo Focus**: a chave `ultima_expectativa_copom`
  em `estado.json`, contendo o último valor processado e a reunião a que ele
  se refere, usada para garantir idempotência e para detectar troca de
  reunião de referência.
- **Notificação de Mudança**: mensagem enviada ao bot dedicado do fluxo
  Focus quando uma mudança relevante é detectada, contendo valor anterior,
  novo valor e identificação da reunião.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Toda mudança relevante na expectativa Focus para a próxima
  reunião do Copom gera exatamente uma notificação no bot dedicado, dentro
  do intervalo de uma execução agendada (nunca mais de uma execução de
  atraso) após a mudança ser publicada pelo Banco Central.
- **SC-002**: Zero notificações duplicadas são enviadas para a mesma mudança
  já processada, mesmo que o sistema rode centenas de execuções agendadas
  consecutivas sem nova mudança publicada.
- **SC-003**: Zero notificações espúrias de "mudança" são geradas
  unicamente por causa da troca da reunião monitorada de uma reunião já
  ocorrida para a próxima.
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
