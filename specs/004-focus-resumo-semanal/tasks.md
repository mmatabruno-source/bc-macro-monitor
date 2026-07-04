---

description: "Task list for feature 004-focus-resumo-semanal"
---

# Tasks: Resumo Semanal do Focus (IPCA, Selic, Câmbio, PIB Total)

**Input**: Design documents from `/specs/004-focus-resumo-semanal/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Incluídos — idempotência e a lógica de comparação justificam testes desde já.

**Organization**: Setup, Foundational (nada novo, reaproveita `src/comum/`), 3 user stories, Polish.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependência)
- **[Story]**: US1, US2 ou US3 (ver spec.md)

## Path Conventions

`src/focus_resumo/` (novo), `src/comum/` (reaproveitado), `tests/`, `historico/focus_resumo/`.

## Phase 1: Setup

- [x] T001 Criar diretório `historico/focus_resumo/` (com `.gitkeep`)

**Checkpoint**: `src/comum/` já existe — nenhuma infraestrutura nova bloqueante.

---

## Phase 2: Foundational

**Purpose**: Nenhuma infraestrutura nova — `http_retry.py` (já com a correção de encoding `%20`), `telegram.py`, `estado.py`, `isolamento.py` são reaproveitados sem alteração.

**Checkpoint**: Nada a fazer além de confirmar que os módulos comuns já existem.

---

## Phase 3: User Story 1 - Receber o resumo semanal dos 4 indicadores (Priority: P1) 🎯 MVP

**Goal**: Detectar nova divulgação (por `Data`) e enviar mensagem com os valores "hoje" de IPCA, Selic, Câmbio e PIB Total para 5 anos, de forma idempotente.

**Independent Test**: Simular checagem com fixture real, verificar mensagem com os 4 indicadores × 5 anos, e que reler a mesma `Data` não duplica.

### Tests for User Story 1

- [x] T002 [P] [US1] Contract test do parser em `tests/contract/test_contrato_focus_resumo.py`, usando `tests/fixtures/expectativas_anuais_2026-06-26.json` e as regras de `contracts/expectativas-anuais.md`
- [x] T003 [P] [US1] Teste de integração do fluxo completo (checar → montar mensagem → notificar → gravar estado) em `tests/integration/test_fluxo_focus_resumo.py`, com API mockada a partir da fixture

### Implementation for User Story 1

- [x] T004 [US1] Implementar `src/focus_resumo/cliente_expectativas_anuais.py`: descobre a `Data` mais recente (Regra 3 do contrato), filtra pelos 4 indicadores com `baseCalculo=0`, retorna lista de `ValorIndicadorAno` para o ano corrente + 4 seguintes (calculados dinamicamente, nunca hardcoded)
- [x] T005 [US1] Implementar `src/focus_resumo/fluxo.py` (esqueleto): checagem (T004) → verificação de idempotência por `data_referencia` → montagem da mensagem (sem direção ainda) → envio → gravação de estado (chave `ultimo_resumo_focus`) SOMENTE após confirmação de envio
- [x] T006 [US1] Implementar gravação de histórico em `historico/focus_resumo/<data_referencia>.json`

**Checkpoint**: User Story 1 completa — MVP (resumo sem direção ainda).

---

## Phase 4: User Story 2 - Ver a comparação com a checagem anterior (Priority: P2)

**Goal**: Cada valor mostra subiu/desceu/manteve contra o valor do mesmo indicador/ano na checagem anterior deste fluxo (sem contador de sequência).

**Independent Test**: Duas checagens consecutivas com valores diferentes para o mesmo indicador/ano; segunda mensagem mostra a direção correta.

### Tests for User Story 2

- [x] T007 [P] [US2] Testes unitários da lógica de comparação em `tests/unit/test_comparador_resumo.py`: subiu/desceu/manteve/sem-histórico, por (indicador, ano) independente dos demais

### Implementation for User Story 2

- [x] T008 [US2] Implementar `src/focus_resumo/comparador.py`: dado o registro anterior (dict `"{indicador}:{ano}" -> valor`, ou ausência) e os novos `ValorIndicadorAno`, retorna a direção por item (sem contador)
- [x] T009 [US2] Integrar `comparador.py` (T008) à montagem da mensagem em `fluxo.py` (T005)

**Checkpoint**: Mensagem completa com direção por item quando há histórico.

---

## Phase 5: User Story 3 - Ser avisado se o fluxo parar de funcionar (Priority: P3)

**Goal**: Falha isolada, sem afetar os outros fluxos.

**Independent Test**: Forçar exceção na checagem; aviso de falha enviado; `estado.json` inalterado; outros fluxos não afetados.

### Tests for User Story 3

- [x] T010 [P] [US3] Teste de integração de falha isolada em `tests/integration/test_fluxo_focus_resumo.py` (mesma suíte de T003)

### Implementation for User Story 3

- [x] T011 [US3] Envolver a chamada ao fluxo em `src/main.py` com `_executar_isolado`, passando `FOCUS_TELEGRAM_BOT_TOKEN`/`FOCUS_TELEGRAM_CHAT_ID` para `notificar_falha`

**Checkpoint**: Todas as três user stories funcionam de forma independente e isolada.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T012 Rodar os cenários 1–4 de `quickstart.md` via suíte automatizada
- [x] T013 Rodar o cenário 5 de `quickstart.md` (chamada real à API) — validado via execução manual do workflow `monitor.yml` no GitHub Actions (run #4, id 28707634573, conclusion: success)
- [x] T014 [P] Revisar logs deste fluxo para confirmar que nenhum token aparece em texto plano (já coberto por `_url_sanitizada`, reaproveitado de `src/comum/http_retry.py`)

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: sem dependências
- **Foundational (Phase 2)**: nada bloqueante
- **User Story 1 (Phase 3)**: depende da Foundational — MVP
- **User Story 2 (Phase 4)**: depende da User Story 1 (estende `fluxo.py`)
- **User Story 3 (Phase 5)**: depende da User Story 1; independente da User Story 2
- **Polish (Phase 6)**: depende de todas as user stories desejadas

### Parallel Opportunities

- T002/T003 podem rodar em paralelo
- T007 é independente de T002-T006

---

## Implementation Strategy

### MVP First (User Story 1)

1. Completar Setup (T001)
2. Completar Phase 3 (User Story 1) — resumo sem direção
3. Validar com `quickstart.md` cenários 1 e 3
4. Deploy do MVP já é possível após User Story 1

### Incremental Delivery

1. User Story 1 → MVP pronto para deploy
2. User Story 2 → direção adicionada
3. User Story 3 → resiliência a falhas
4. Polish

## Notes

- [P] tasks = arquivos diferentes, sem dependência
- Um commit por tarefa (`T0XX: <resumo>`), conforme Princípio I
- Contrato já verificado com payload real antes desta lista de tarefas
  existir, conforme Princípio II
