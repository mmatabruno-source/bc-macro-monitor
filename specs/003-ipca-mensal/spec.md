# Feature Specification: Notificação da Divulgação Mensal do IPCA

**Feature Branch**: `003-ipca-mensal`

**Created**: 2026-07-03

**Status**: Draft

**Input**: User description: "Notificar a divulgação mensal do IPCA com leitura objetiva do número e breve leitura de impacto para portfólio"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ser avisado assim que o IPCA do mês é divulgado (Priority: P1)

Como acompanhante de política monetária para apoio a decisões de portfólio,
quero ser avisado no Telegram assim que o IPCA do mês for divulgado, com o
número objetivo (variação mensal, e acumulados relevantes se disponíveis),
para não depender de checar o calendário do IBGE/BCB manualmente todo mês.

**Why this priority**: É o núcleo do fluxo — sem detecção da divulgação não
há produto. O IPCA é o principal input observado de inflação corrente, com
efeito direto sobre expectativas de juros.

**Independent Test**: Pode ser testado simulando duas checagens consecutivas
da série do IPCA, uma sem o dado do mês novo e outra com ele, verificando
que uma notificação é enviada ao bot dedicado deste fluxo somente quando o
novo valor mensal aparece, e que o valor é registrado em `estado.json`
somente após a notificação ser confirmada como enviada.

**Acceptance Scenarios**:

1. **Given** o último valor de IPCA registrado em `estado.json` é o do mês
   anterior, **When** a checagem periódica encontra um novo valor mensal na
   série oficial, **Then** o sistema envia uma notificação ao bot do fluxo
   IPCA com o número objetivo do mês, e só então registra o novo valor como
   processado.
2. **Given** o último valor registrado já é o mais recente disponível na
   série, **When** a checagem periódica roda novamente, **Then** nenhuma
   notificação é enviada e `estado.json` não é alterado (idempotência).

---

### User Story 2 - Receber uma leitura breve de impacto para portfólio, não só o número (Priority: P2)

Como usuário do monitor, quero que a notificação inclua uma leitura curta do
que o resultado do IPCA implica para o posicionamento de portfólio (ex.:
pressiona ou alivia expectativa de juros), além do número em si — mas de
forma direta e curta, sem a profundidade de análise usada nos fluxos de Ata
ou Relatório, já que aqui é um número pontual, não um documento extenso.

**Why this priority**: Aumenta o valor do fluxo além de um simples "saiu o
número", mas o fluxo já entrega valor mínimo sem isso (User Story 1) — por
isso é P2, não P1.

**Independent Test**: Pode ser testado fornecendo um valor de IPCA de teste
ao gerador de leitura e verificando que a notificação inclui, além do
número, uma frase curta de leitura de impacto para portfólio, sem inflar a
mensagem em múltiplas mensagens sequenciais como nos outros fluxos.

**Acceptance Scenarios**:

1. **Given** um novo valor de IPCA foi detectado (User Story 1), **When**
   o sistema monta a notificação, **Then** ele envia uma única mensagem ao
   bot do fluxo IPCA contendo o número objetivo (variação mensal, e
   acumulados relevantes se disponíveis na mesma série) e uma leitura curta
   de impacto para portfólio.

---

### User Story 3 - Ser avisado se o fluxo parar de funcionar (Priority: P3)

Como usuário do monitor, quero ser avisado no bot do fluxo IPCA se uma
checagem falhar de forma inesperada, para saber que preciso investigar.

**Why this priority**: Camada de robustez, consistente com os outros dois
fluxos do repositório — não é o núcleo do produto, mas aumenta a confiança
no sistema.

**Independent Test**: Forçar uma exceção durante a checagem (ex.: série
indisponível) e verificar que uma notificação de falha é enviada ao bot do
fluxo IPCA, que os outros dois fluxos do repositório não são afetados, e
que `estado.json` não é alterado para este fluxo.

**Acceptance Scenarios**:

1. **Given** a série do IPCA está indisponível ou retorna um formato
   inesperado durante uma checagem, **When** a execução agendada roda,
   **Then** o sistema captura o erro, envia um aviso de falha ao bot do
   fluxo IPCA, não modifica `estado.json` para este fluxo, e permite que os
   outros dois fluxos executem normalmente na mesma execução.

---

### Edge Cases

- O que acontece na primeiríssima execução do fluxo, sem nenhum valor
  registrado em `estado.json`? O valor mais recente disponível na série é
  registrado como baseline processado, com notificação enviada normalmente
  (cada divulgação mensal é um evento discreto, como no fluxo de
  Relatório, não uma série contínua a comparar como no fluxo Focus).
- O que acontece se a série for revisada retroativamente pelo IBGE/BCB
  (valor de um mês já processado mudar depois)? Fora de escopo desta spec —
  o sistema reage apenas à chegada de um novo mês na série, não a revisões
  de meses já notificados. Comportamento exato de detecção de revisão
  depende do contrato real da série (ver Assumptions).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST checar periodicamente (execução agendada
  diária) a série oficial do IPCA (SGS, série 433) para identificar se um
  novo valor mensal foi divulgado.
- **FR-002**: O sistema MUST identificar um valor como "novo" quando se
  referir a um mês de referência ainda não registrado como processado em
  `estado.json`.
- **FR-003**: O sistema MUST enviar, ao detectar um novo valor mensal, uma
  notificação ao bot do Telegram dedicado a este fluxo, contendo o número
  objetivo (variação mensal, e outros valores relevantes disponíveis na
  mesma série) e uma leitura curta de impacto para portfólio.
- **FR-004**: O sistema MUST registrar o novo valor mensal como processado
  em `estado.json` SOMENTE depois que a notificação for confirmada como
  enviada com sucesso.
- **FR-005**: O sistema MUST NOT enviar uma segunda notificação para um mês
  já registrado como processado (idempotência).
- **FR-006**: O sistema MUST isolar falhas deste fluxo de forma que uma
  exceção inesperada durante a checagem não impeça a execução ou
  notificação dos outros dois fluxos (Focus, Relatório) na mesma execução
  agendada.
- **FR-007**: O sistema MUST notificar falhas inesperadas deste fluxo
  especificamente ao bot dedicado ao fluxo IPCA, nunca a um bot de outro
  fluxo.
- **FR-008**: O sistema MUST usar a série oficial do IPCA como única fonte
  de verdade para decidir se um novo valor mensal foi divulgado, nunca um
  calendário estimado de datas de divulgação (calendário pode, no máximo,
  informar que a checagem pode ser feita com frequência reduzida fora da
  janela usual de divulgação, nunca decidir se a checagem ocorre).
- **FR-009**: A geração da leitura de impacto para portfólio MUST usar
  [NEEDS CLARIFICATION: a leitura de impacto usa um LLM (como os fluxos de
  Ata/Relatório) para interpretar o número, ou é uma formatação direta
  baseada em regras simples (ex.: "acima/abaixo do centro da meta",
  "acelerou/desacelerou em relação ao mês anterior")? Não deve ser assumido
  que precisa de LLM só porque os outros fluxos usam — aqui não há "tom" de
  texto a interpretar, apenas um número].

### Key Entities *(include if feature involves data)*

- **Divulgação Mensal do IPCA**: representa o valor da série 433 (SGS)
  referente a um mês específico, identificado por mês de referência e
  valor (variação percentual).
- **Registro de Estado do Fluxo IPCA**: a chave `ultimo_ipca` em
  `estado.json`, contendo o mês de referência e valor do último dado
  processado com sucesso.
- **Leitura de Impacto para Portfólio**: texto curto anexado à notificação,
  interpretando o que o valor do IPCA implica para expectativas de juros —
  o mecanismo exato de geração (LLM vs. regra direta) depende de FR-009.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Toda nova divulgação mensal do IPCA gera exatamente uma
  notificação no bot dedicado, dentro do intervalo de uma execução agendada
  (nunca mais de uma execução de atraso) após a divulgação.
- **SC-002**: Zero notificações duplicadas são enviadas para o mesmo mês já
  processado, mesmo que o sistema rode centenas de execuções agendadas
  consecutivas sem nova divulgação.
- **SC-003**: 100% das notificações enviadas contêm tanto o número objetivo
  quanto uma leitura de impacto para portfólio na mesma mensagem.
- **SC-004**: Uma falha inesperada neste fluxo nunca impede que os outros
  dois fluxos monitorados pelo mesmo sistema completem sua checagem e
  notificação na mesma execução.

## Assumptions

- A série 433 do SGS é atualizada tempestivamente após cada divulgação
  mensal do IPCA (dado espelhado do IBGE), e uma checagem agendada diária é
  suficiente para não gerar atraso relevante para decisões de portfólio.
- Existe um bot do Telegram dedicado a este fluxo (`IPCA_TELEGRAM_BOT_TOKEN`
  / `IPCA_TELEGRAM_CHAT_ID`), a ser criado e configurado como GitHub Secret
  antes do primeiro deploy — fora do escopo desta spec.
- O formato exato do payload da série (campos, granularidade, se traz
  núcleos de inflação na mesma consulta ou exige séries adicionais) ainda
  não foi verificado por uma chamada de teste real — por princípio deste
  projeto, nenhum cliente HTTP ou parser será escrito até que o usuário
  forneça a resposta real de uma chamada de teste a
  `bcdata.sgs.433/dados/ultimos/N`; esta spec descreve apenas o
  comportamento esperado, não a estrutura de dados da série.
- Núcleos de inflação (séries adicionais do SGS) são tratados como "se
  disponíveis" na mesma consulta — se exigirem uma chamada a uma série SGS
  diferente, ficam fora do escopo mínimo deste fluxo (FR-003 exige apenas o
  número objetivo da série 433), podendo ser adicionados como melhoria
  futura sem alterar o núcleo do fluxo.
