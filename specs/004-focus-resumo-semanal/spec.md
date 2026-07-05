# Feature Specification: Resumo Semanal do Focus (IPCA, Selic, Câmbio, PIB Total)

**Feature Branch**: `004-focus-resumo-semanal`

**Created**: 2026-07-04

**Status**: Draft

**Input**: User description: "Resumo semanal do Focus com IPCA, Selic, Câmbio e PIB Total, valor de hoje para os próximos 5 anos, com comparação vs há 1 semana via histórico próprio, sem contador de sequência"

> **Atualização (2026-07-05, trilha leve — ver `research.md`)**: dois
> pontos mudaram depois da implementação inicial, por pedido do usuário:
> 1. Reduzido de 5 para **4 anos no total** (ano corrente + 3 seguintes),
>    não 4 seguintes.
> 2. A indicação de direção (FR-004) deixou de ser texto
>    "(subiu)/(desceu)/(manteve)" e virou seta com a magnitude da
>    variação entre parênteses: `(▲ X,XX p.p.)` / `(▼ X,XX p.p.)` /
>    `(= 0 p.p.)`. Títulos de indicador também ganharam unidade explícita
>    (`IPCA (a.a.)`, `Câmbio (BRL/USD)`, `PIB (var. sobre o ano anterior)`,
>    com sufixo `%` nos valores do PIB).
> As FRs/SC/Assumptions abaixo foram atualizadas para o estado atual; os
> User Scenarios (narrativa original) permanecem como registro histórico
> do pedido inicial.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Receber um resumo semanal dos 4 principais indicadores do Focus (Priority: P1)

Como acompanhante de política monetária para apoio a decisões de portfólio,
quero receber uma vez por semana um resumo com o valor mais recente do
Focus para IPCA, Selic, Câmbio e PIB Total, para os próximos 5 anos
(ano corrente + 4 seguintes), sem precisar abrir o boletim completo do BCB.

**Why this priority**: É o núcleo do fluxo — sem isso não há produto. É o
complemento natural ao fluxo Focus/Copom já existente (que só cobre Selic
para a próxima reunião): este resumo dá visão ampla dos 4 indicadores mais
citados em decisão de portfólio.

**Independent Test**: Pode ser testado simulando uma checagem semanal com
uma fixture de valores anuais, verificando que a mensagem gerada contém os
4 indicadores, cada um com os valores dos 5 anos cobertos.

**Acceptance Scenarios**:

1. **Given** é o dia da checagem semanal, **When** o sistema consulta a API
   de expectativas anuais, **Then** ele envia uma mensagem ao bot com o
   valor "hoje" de IPCA, Selic, Câmbio e PIB Total para o ano corrente e os
   4 anos seguintes.
2. **Given** o resumo já foi enviado para a divulgação da semana atual,
   **When** o sistema checa novamente antes da próxima divulgação
   semanal, **Then** nenhuma mensagem duplicada é enviada.

---

### User Story 2 - Ver a comparação com a semana anterior (Priority: P2)

Como usuário do monitor, quero que cada valor do resumo mostre se
subiu, desceu ou manteve em relação à divulgação da semana anterior, para
identificar rapidamente o que mudou sem ter que guardar o resumo anterior
para comparar manualmente.

**Why this priority**: Aumenta o valor do resumo (contexto de tendência),
mas o fluxo já entrega valor mínimo sem isso (User Story 1) — por isso é
P2, não P1.

**Independent Test**: Pode ser testado simulando duas checagens semanais
consecutivas com valores diferentes para o mesmo indicador/ano, e
verificando que a segunda mensagem indica a direção (subiu/desceu/manteve)
com base no valor guardado da primeira checagem.

**Acceptance Scenarios**:

1. **Given** um valor de IPCA/ano já foi registrado numa checagem semanal
   anterior, **When** a nova checagem semanal encontra um valor diferente
   para o mesmo indicador/ano, **Then** a mensagem indica a direção
   (subiu/desceu/manteve) comparando com o valor da checagem anterior
   registrada no histórico do próprio sistema (não com o "há 1 semana" que
   o boletim oficial do BCB calcula).
2. **Given** é a primeira checagem semanal já realizada para um
   indicador/ano (sem histórico próprio anterior), **When** o resumo é
   montado, **Then** o valor aparece sem indicação de direção (não há
   comparação possível ainda).

---

### User Story 3 - Ser avisado se o fluxo parar de funcionar (Priority: P3)

Como usuário do monitor, quero ser avisado se a checagem semanal falhar de
forma inesperada, para saber que preciso investigar.

**Why this priority**: Camada de robustez, consistente com os demais
fluxos do repositório — não é o núcleo do produto.

**Independent Test**: Forçar uma exceção durante a checagem (ex.: API
indisponível) e verificar que uma notificação de falha é enviada, que o
histórico não é alterado, e que os outros fluxos do repositório não são
afetados.

**Acceptance Scenarios**:

1. **Given** a API de expectativas anuais está indisponível ou retorna um
   formato inesperado durante a checagem semanal, **When** a execução
   agendada roda, **Then** o sistema captura o erro, envia um aviso de
   falha, não modifica o histórico deste fluxo, e permite que os outros
   fluxos do repositório executem normalmente na mesma execução.

---

### Edge Cases

- O que acontece na primeira semana em que o fluxo roda, sem nenhum
  histórico próprio anterior? Todos os valores aparecem sem indicação de
  direção (ver User Story 2, cenário 2) — não há como recuperar
  comparações de antes do fluxo existir.
- O que acontece se a divulgação semanal do Focus atrasar (ex.: feriado)?
  O sistema não assume uma data fixa de divulgação — a checagem é diária,
  mas só considera "nova divulgação semanal" quando a API retornar uma
  `Data` mais recente que a última registrada no histórico deste fluxo
  (mesma lógica de idempotência por data usada no fluxo Focus/Copom
  existente).
- O que acontece se um dos 4 indicadores não tiver valor disponível para
  algum dos 5 anos (ex.: ano muito distante, poucos respondentes)? O
  resumo mostra os anos disponíveis e omite o que não veio na resposta,
  sem quebrar o envio dos demais.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST checar periodicamente (execução agendada) a
  API de expectativas anuais do Focus para os indicadores IPCA, Selic,
  Câmbio e PIB Total.
- **FR-002**: O sistema MUST considerar uma nova divulgação semanal quando
  a API retornar uma data de referência mais recente que a última
  registrada no histórico deste fluxo.
- **FR-003**: O sistema MUST enviar, a cada nova divulgação semanal, uma
  mensagem contendo o valor "hoje" de cada um dos 4 indicadores, para o
  ano corrente e os 3 anos seguintes (4 anos no total — ver Atualização).
- **FR-004**: O sistema MUST indicar a direção de cada valor comparado ao
  valor do mesmo indicador/ano registrado na checagem semanal anterior
  deste fluxo — nunca ao "há 1 semana" que o boletim oficial já calcula
  internamente — exibida como seta com a magnitude da variação em p.p.
  entre parênteses (`(▲ X,XX p.p.)` / `(▼ X,XX p.p.)` / `(= 0 p.p.)`, ver
  Atualização acima).
- **FR-005**: O sistema MUST omitir a indicação de direção para
  combinações indicador/ano sem registro anterior no histórico deste
  fluxo (primeira leitura).
- **FR-006**: O sistema MUST NOT usar nem exibir nenhum contador de
  quantas semanas consecutivas um comportamento se repete — apenas a
  direção da última comparação.
- **FR-007**: O sistema MUST registrar os valores da divulgação processada
  no histórico deste fluxo SOMENTE depois que o envio da mensagem for
  confirmado como bem-sucedido.
- **FR-008**: O sistema MUST NOT enviar uma segunda mensagem para uma
  divulgação semanal já processada (idempotência por data de referência).
- **FR-009**: O sistema MUST isolar falhas deste fluxo de forma que uma
  exceção inesperada durante a checagem não impeça a execução ou
  notificação dos outros fluxos do repositório na mesma execução agendada.
- **FR-010**: O sistema MUST usar a API oficial de expectativas anuais
  como única fonte de verdade para os valores e para a data da divulgação,
  nunca um calendário estimado.

### Key Entities *(include if feature involves data)*

- **ResumoSemanalFocus**: representa a divulgação processada numa
  checagem, contendo a data de referência e os valores dos 4 indicadores
  para os 4 anos cobertos (ver Atualização acima).
- **ValorIndicadorAno**: um par (indicador, ano) com seu valor mais
  recente e, se houver histórico anterior, a direção comparada a ele.
- **Registro de Estado/Histórico deste Fluxo**: guarda, por
  indicador/ano, o último valor processado, usado apenas para calcular a
  direção da próxima checagem (FR-004) e para a idempotência por data
  (FR-008).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Toda nova divulgação semanal do Focus gera exatamente uma
  mensagem de resumo, dentro do intervalo de uma execução agendada após a
  divulgação.
- **SC-002**: Zero mensagens duplicadas para a mesma divulgação semanal já
  processada.
- **SC-003**: 100% dos valores exibidos no resumo correspondem ao ano
  corrente e aos 3 anos seguintes, para os 4 indicadores definidos (IPCA,
  Selic, Câmbio, PIB Total).
- **SC-004**: Uma falha inesperada neste fluxo nunca impede que os outros
  fluxos monitorados pelo mesmo sistema completem sua checagem e
  notificação na mesma execução.

## Assumptions

- Este resumo é enviado ao mesmo bot do Telegram já usado pelo fluxo
  Focus/Copom existente (`FOCUS_TELEGRAM_BOT_TOKEN`/`FOCUS_TELEGRAM_CHAT_ID`),
  por ser o mesmo domínio temático (Focus) — não é criado um bot novo para
  este fluxo, a menos que o usuário indique o contrário na fase de
  planejamento.
- O ano corrente e os 3 anos seguintes são calculados a partir da data de
  execução do sistema (ano atual + 3), não de uma lista fixa de anos.
- O formato exato do payload da API de expectativas anuais já foi
  verificado por chamadas de teste reais em 2026-07-04 (ver
  `research.md`/`contracts/` na fase de planejamento) — os nomes reais de
  campo (`Indicador`, `DataReferencia`, `Mediana`, `Data`, `baseCalculo`)
  já são conhecidos, então este fluxo não fica bloqueado pelo Princípio II
  ao entrar em `/speckit-plan`.
- Este fluxo reaproveita a infraestrutura comum já construída
  (`src/comum/`) e o padrão de idempotência/isolamento de falha dos
  fluxos existentes.
