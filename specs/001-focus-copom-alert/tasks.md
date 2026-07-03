---

description: "Task list for feature 001-focus-copom-alert"
---

# Tasks: Alerta de Mudança Relevante no Focus para a Próxima Reunião do Copom

**Input**: Design documents from `/specs/001-focus-copom-alert/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Incluídos — a lógica de comparação e idempotência é crítica o suficiente (Princípios II e V da constituição) para justificar testes desde já.

**Organization**: Tarefas agrupadas por user story (US1, US2, US3) do spec.md, com uma fase de Setup, uma Foundational, e uma final de Polish.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependência)
- **[Story]**: US1, US2 ou US3 (ver spec.md)
- **[BLOCKED]**: Tarefa bloqueada pelo Princípio II da constituição (contrato de API não verificado) — não iniciar antes de T004 ser concluída

## Path Conventions

Projeto único (single project), conforme `plan.md`: `src/`, `tests/`, `estado.json`, `historico/focus/` na raiz do repositório.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialização do projeto e estrutura básica compartilhada pelos três fluxos do repositório (este é o primeiro fluxo implementado, então a estrutura comum nasce aqui).

- [ ] T001 Criar estrutura de diretórios `src/comum/`, `src/focus/`, `tests/contract/`, `tests/integration/`, `tests/unit/`, `historico/focus/` conforme `plan.md`
- [ ] T002 Criar `requirements.txt` na raiz com `requests` e `pytest` (únicas dependências, por Princípio VII)
- [ ] T003 [P] Criar `estado.json` inicial na raiz com objeto vazio `{}` (chaves por fluxo são adicionadas em runtime)

**Checkpoint**: Estrutura pronta para receber código de infraestrutura comum e do fluxo Focus.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestrutura compartilhada pelos três fluxos do repositório (retry HTTP, envio ao Telegram, estado, isolamento de execução) — nasce neste primeiro fluxo e será reaproveitada pelos fluxos 002 e 003.

**⚠️ CRITICAL**: Nenhuma tarefa de user story pode começar antes desta fase estar completa.

- [ ] T004 **[BLOCKED — Princípio II]** Solicitar ao usuário o payload JSON real de uma chamada de teste ao endpoint candidato `ExpectativasMercadoSelic` (Olinda) e preencher `specs/001-focus-copom-alert/contracts/focus-api.md` com o schema observado. **Não prosseguir para T012–T015 (implementação do cliente HTTP e parser) enquanto esta tarefa não estiver concluída.**
- [ ] T005 [P] Implementar `_retentavel(status_code)` e `_espera_para_tentativa(resposta, tentativa)` em `src/comum/http_retry.py`, adaptados do padrão validado no copom-monitor-pm (retry em 429/5xx, respeita `Retry-After`, nunca retenta 4xx permanente)
- [ ] T006 [P] Implementar `enviar_mensagem(texto, token, chat_id)` com fallback de formatação Markdown → texto simples e `_sanitizar(texto, token)` em `src/comum/telegram.py`, reaproveitando a assinatura do copom-monitor-pm
- [ ] T007 [P] Implementar leitura/escrita de `estado.json` por chave de fluxo em `src/comum/estado.py` (funções `ler_estado(chave)` e `gravar_estado(chave, valor)`, sem depender do formato interno de nenhum fluxo específico)
- [ ] T008 [P] Implementar `_executar_isolado(nome, verificar)` em `src/comum/isolamento.py`, reaproveitado do copom-monitor-pm, e `notificar_falha(contexto, erro, token, chat_id)` parametrizado por bot/chat (Princípio IV — sem bot padrão)
- [ ] T009 Criar `src/main.py` como ponto de entrada único do GitHub Actions, chamando o fluxo Focus através de `_executar_isolado` (T008); estrutura para os fluxos 002/003 será adicionada em features futuras, sem implementá-los aqui
- [ ] T010 [P] Testes unitários de `src/comum/http_retry.py` em `tests/unit/test_http_retry.py` (retenta 429/5xx, respeita `Retry-After`, não retenta 404)
- [ ] T011 [P] Testes unitários de `src/comum/estado.py` em `tests/unit/test_estado.py` (leitura/escrita por chave, chave ausente retorna `None`/vazio sem exceção)

**Checkpoint**: Infraestrutura comum pronta e testada — user stories do fluxo Focus podem começar. T004 permanece como bloqueio explícito até resolvida.

---

## Phase 3: User Story 1 - Ser avisado a cada divulgação do Focus (Priority: P1) 🎯 MVP

**Goal**: A cada nova divulgação do boletim Focus para a próxima reunião do Copom, enviar notificação ao bot dedicado com comparação subiu/desceu/manteve, de forma idempotente.

**Independent Test**: Simular duas divulgações consecutivas (fixtures com `data_referencia` distintas) e verificar que uma notificação é enviada a cada uma, com a direção correta, e que reler a mesma divulgação não gera notificação duplicada.

### Tests for User Story 1

- [ ] T012 [P] [US1] **[BLOCKED até T004]** Contract test do parser da API Focus em `tests/contract/test_contrato_focus.py`, usando o payload real documentado em `contracts/focus-api.md`
- [ ] T013 [P] [US1] Testes unitários da lógica de comparação (subiu/desceu/manteve/inicial) em `tests/unit/test_comparador.py`, usando fixtures de `DivulgacaoFocus` simuladas (independe do contrato real da API)
- [ ] T014 [P] [US1] Teste de integração do fluxo completo (checar → comparar → notificar → gravar estado) em `tests/integration/test_fluxo_focus.py`, com API Focus mockada a partir de fixtures

### Implementation for User Story 1

- [ ] T015 [US1] **[BLOCKED até T004]** Implementar `src/focus/cliente_expectativas.py`: cliente HTTP para o endpoint Focus (usa `src/comum/http_retry.py`), retornando a mediana da Selic e a data de referência para a próxima reunião, conforme `contracts/focus-api.md`
- [ ] T016 [US1] Implementar `src/focus/comparador.py`: dado o registro anterior (ou ausência dele) e a nova `DivulgacaoFocus`, retorna a direção (`subiu`/`desceu`/`manteve`/`inicial`) conforme `data-model.md`
- [ ] T017 [US1] Implementar `src/focus/fluxo.py`: orquestra checagem (T015) → comparação (T016) → montagem da mensagem de notificação → envio via `enviar_mensagem` (T006) → gravação de estado via `src/comum/estado.py` (T007) SOMENTE após confirmação de envio bem-sucedido (FR-006)
- [ ] T018 [US1] Implementar gravação de histórico em `historico/focus/<data_referencia>.json` a cada divulgação processada com sucesso, em `src/focus/fluxo.py`
- [ ] T019 [US1] Adicionar logging estruturado (sem vazar token) nas etapas de `src/focus/fluxo.py`, usando `_sanitizar` (T006) em qualquer log que inclua resposta/erro de rede

**Checkpoint**: User Story 1 completa e testável de forma independente — este é o MVP do fluxo Focus.

---

## Phase 4: User Story 2 - Continuar funcionando após a reunião do Copom passar (Priority: P2)

**Goal**: Identificar automaticamente a nova "próxima reunião" a partir da API oficial quando a reunião monitorada anteriormente já ocorreu, sem gerar comparação espúria.

**Independent Test**: Simular uma fixture em que a `reuniao_id` observada na API é diferente da registrada em `estado.json`, e verificar que o sistema passa a monitorar a nova reunião com notificação informativa (`direcao: inicial`), sem comparar contra o valor da reunião anterior.

### Tests for User Story 2

- [ ] T020 [P] [US2] Teste unitário de troca de reunião monitorada em `tests/unit/test_comparador.py` (mesma suíte de T013): `reuniao_id` nova → `direcao: inicial`, sem comparação numérica contra a reunião anterior
- [ ] T021 [P] [US2] Teste de integração de rollover de reunião em `tests/integration/test_fluxo_focus.py` (mesma suíte de T014): estado aponta para reunião já passada, API retorna a próxima reunião real

### Implementation for User Story 2

- [ ] T022 [US2] Estender `src/focus/comparador.py` (T016) para detectar mudança de `reuniao_id` em relação ao estado registrado e tratar como primeira leitura da nova reunião (reaproveita a mesma lógica de "sem baseline" da User Story 1, FR-008)
- [ ] T023 [US2] Garantir em `src/focus/cliente_expectativas.py` (T015) que a "próxima reunião" é sempre recalculada a partir da resposta da API a cada execução, nunca de um valor fixo ou cacheado além do necessário para a checagem atual (Princípio VI)

**Checkpoint**: User Stories 1 e 2 funcionam juntas — o fluxo sobrevive à passagem de reuniões sem intervenção manual.

---

## Phase 5: User Story 3 - Ser avisado se o fluxo parar de funcionar (Priority: P3)

**Goal**: Se a checagem falhar de forma inesperada, notificar o bot dedicado ao fluxo Focus sem afetar os outros fluxos do repositório nem alterar `estado.json`.

**Independent Test**: Forçar uma exceção durante a checagem (ex.: resposta HTTP malformada) e verificar que uma notificação de falha é enviada ao bot do fluxo Focus, que `estado.json` permanece inalterado para este fluxo, e que a execução de outro fluxo simulado no mesmo processo não é interrompida.

### Tests for User Story 3

- [ ] T024 [P] [US3] Teste de integração de falha isolada em `tests/integration/test_fluxo_focus.py` (mesma suíte de T014/T021): exceção durante checagem → `notificar_falha` chamado com token/chat_id do fluxo Focus, `estado.json` inalterado
- [ ] T025 [P] [US3] Teste unitário de `_executar_isolado` (T008, já parcialmente coberto em foundational) com um "fluxo" fake que lança exceção, confirmando que a exceção não se propaga, em `tests/unit/test_isolamento.py`

### Implementation for User Story 3

- [ ] T026 [US3] Envolver a chamada ao fluxo Focus em `src/main.py` (T009) com `_executar_isolado` (T008), passando o nome do fluxo e o bot/chat_id do fluxo Focus para `notificar_falha`
- [ ] T027 [US3] Garantir em `src/focus/fluxo.py` (T017) que qualquer exceção não tratada durante a checagem propaga para `_executar_isolado` sem gravar estado parcial em `estado.json`

**Checkpoint**: Todas as três user stories do fluxo Focus funcionam de forma independente e isolada.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Melhorias que afetam o fluxo como um todo, e preparação para o watchdog e para o workflow do GitHub Actions.

- [ ] T028 [P] Criar workflow do GitHub Actions (`.github/workflows/focus-copom.yml`) que roda `src/main.py` em cron diário, injetando `FOCUS_TELEGRAM_BOT_TOKEN` e `FOCUS_TELEGRAM_CHAT_ID` via GitHub Secrets (Princípio IX)
- [ ] T029 Rodar os cenários de `quickstart.md` manualmente (1 a 5, sem depender da API real) e confirmar os resultados esperados
- [ ] T030 **[BLOCKED até T004]** Rodar o cenário 6 de `quickstart.md` (chamada real à API Focus) e confirmar que o parser funciona contra a API de produção
- [ ] T031 [P] Revisar todos os logs e mensagens de erro do fluxo Focus para confirmar que nenhum token aparece em texto plano (Princípio IX)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências — pode começar imediatamente
- **Foundational (Phase 2)**: Depende do Setup. T004 (payload real da API) bloqueia T012 e T015 na Phase 3, mas não bloqueia T005–T011
- **User Story 1 (Phase 3)**: Depende da Foundational completa. É o MVP
- **User Story 2 (Phase 4)**: Depende da User Story 1 (estende `comparador.py` e `cliente_expectativas.py` criados ali)
- **User Story 3 (Phase 5)**: Depende da Foundational (T008/T009) e da User Story 1 (`fluxo.py`); independente da User Story 2
- **Polish (Phase 6)**: Depende de todas as user stories desejadas estarem completas; T030 depende de T004

### Parallel Opportunities

- T005–T008 (Foundational, arquivos diferentes) podem rodar em paralelo
- T010–T011 (testes unitários de infraestrutura) podem rodar em paralelo entre si e com T005–T008 já concluídas
- T013–T014 podem rodar em paralelo com T012 (T012 fica bloqueada por T004, mas T013/T014 não dependem do contrato real)
- T020–T021 podem rodar em paralelo entre si

---

## Implementation Strategy

### MVP First (User Story 1)

1. Completar Phase 1 (Setup) e Phase 2 (Foundational) — **exceto T004, que pode ficar pendente sem bloquear T005–T011**
2. Pedir ao usuário o payload real da API (T004) o quanto antes, em paralelo ao resto da Foundational
3. Completar Phase 3 (User Story 1) assim que T004 for resolvida para as tarefas T012/T015; as demais tarefas de US1 não dependem de T004
4. **PARAR e VALIDAR**: rodar `quickstart.md` cenários 1–3 antes de prosseguir
5. Deploy do MVP (workflow do GitHub Actions) já é possível após User Story 1

### Incremental Delivery

1. Setup + Foundational → base pronta (com T004 como pendência sinalizada, não bloqueante do todo)
2. User Story 1 → validar independentemente → MVP pronto para deploy
3. User Story 2 → validar independentemente → fluxo sobrevive à passagem de reuniões
4. User Story 3 → validar independentemente → fluxo resiliente a falhas
5. Polish → workflow de produção e revisão final de segredos

## Notes

- [P] tasks = arquivos diferentes, sem dependência
- Um commit por tarefa (`T0XX: <resumo>`), conforme Princípio I da constituição
- T004 é a tarefa mais crítica do ponto de vista de processo: nenhuma linha de `src/focus/cliente_expectativas.py` ou `tests/contract/test_contrato_focus.py` deve ser escrita antes dela
- Verificar que os testes falham antes de implementar (quando aplicável)
