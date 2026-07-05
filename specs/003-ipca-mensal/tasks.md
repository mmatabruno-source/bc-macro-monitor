---

description: "Task list for feature 003-ipca-mensal"
---

# Tasks: Notificação da Divulgação Mensal do IPCA

**Input**: Design documents from `/specs/003-ipca-mensal/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

> **Nota (2026-07-05, trilha leve)**: as tasks abaixo cobrem só a
> implementação original (mês/valor + leitura qualitativa). A composição
> por grupo, o detalhamento por item dos top-3 grupos e a substituição da
> leitura qualitativa por valores explícitos (variação anualizada + meta)
> foram implementados depois, por edição direta — ver `research.md` e
> `decisoes/composicao-ipca-por-grupo.md` para o registro completo, e
> `data-model.md`/`spec.md` (FR-003a) para o estado atual. Sem `tasks.md`
> formal para essas adições — cobertas por
> `tests/contract/test_contrato_ipca_composicao.py`,
> `test_contrato_ipca_itens.py` e os testes de
> `tests/integration/test_fluxo_ipca.py`.

**Tests**: Incluídos — idempotência e a regra de leitura de impacto justificam testes desde já.

**Organization**: Tarefas agrupadas por user story (US1, US2, US3), com Setup, Foundational (mínima, reaproveita `src/comum/` do fluxo 001) e Polish.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependência)
- **[Story]**: US1, US2 ou US3 (ver spec.md)

## Path Conventions

Projeto único: `src/ipca/` (novo), `src/comum/` (reaproveitado do fluxo 001), `tests/`, `historico/ipca/`.

## Phase 1: Setup

- [x] T001 Criar diretório `historico/ipca/` (com `.gitkeep`)

**Checkpoint**: `src/comum/` já existe do fluxo 001 — nenhuma infraestrutura nova necessária.

---

## Phase 2: Foundational

**Purpose**: Nenhuma infraestrutura nova bloqueante — `src/comum/http_retry.py`, `telegram.py`, `estado.py` e `isolamento.py` já existem e são reaproveitados sem alteração estrutural.

**Checkpoint**: Nada a fazer nesta fase além de confirmar que os módulos comuns já existem.

---

## Phase 3: User Story 1 - Ser avisado a cada divulgação mensal do IPCA (Priority: P1) 🎯 MVP

**Goal**: A cada novo mês de referência divulgado na série 433, enviar notificação ao bot dedicado com o número objetivo, de forma idempotente.

**Independent Test**: Simular duas checagens consecutivas (fixture com mês novo vs. mês já processado) e verificar que a notificação só é enviada quando há mês novo, e que reler o mesmo mês não gera notificação duplicada.

### Tests for User Story 1

- [x] T002 [P] [US1] Contract test do parser da série IPCA em `tests/contract/test_contrato_ipca.py`, usando `tests/fixtures/ipca_ultimos_3.json` e as regras de `contracts/ipca-sgs.md`
- [x] T003 [P] [US1] Teste de integração do fluxo completo (checar → notificar → gravar estado) em `tests/integration/test_fluxo_ipca.py`, com API mockada a partir da fixture

### Implementation for User Story 1

- [x] T004 [US1] Implementar `src/ipca/cliente_sgs.py`: cliente HTTP para `bcdata.sgs.433/dados/ultimos/2` (usa `src/comum/http_retry.py`), convertendo `data`/`valor` conforme `contracts/ipca-sgs.md`, retornando o `DivulgacaoIpca` do mês mais recente
- [x] T005 [US1] Implementar `src/ipca/fluxo.py`: orquestra checagem (T004) → verificação de idempotência (mês já processado?) → montagem da mensagem → envio via `enviar_mensagem` → gravação de estado (chave `ultimo_ipca`) SOMENTE após confirmação de envio bem-sucedido
- [x] T006 [US1] Implementar gravação de histórico em `historico/ipca/<mes_referencia>.json` a cada mês processado com sucesso, em `src/ipca/fluxo.py`

**Checkpoint**: User Story 1 completa — MVP do fluxo IPCA.

---

## Phase 4: User Story 2 - Leitura de impacto para portfólio (Priority: P2)

**Goal**: Cada notificação inclui uma leitura curta e determinística (sem LLM) de impacto: comparação com o mês anterior e com o centro da meta de inflação.

**Independent Test**: Fornecer um valor de teste e verificar que a notificação inclui a frase de leitura de impacto, calculada corretamente contra o mês anterior e a meta.

### Tests for User Story 2

- [x] T007 [P] [US2] Testes unitários da regra de leitura de impacto em `tests/unit/test_leitura_impacto.py`: `acelerou`/`desacelerou`/`estavel` vs. mês anterior; `acima`/`abaixo`/`em_linha` vs. meta

### Implementation for User Story 2

- [x] T008 [US2] Implementar `src/ipca/leitura_impacto.py`: constante `META_INFLACAO_CENTRO` e função `gerar_leitura(mes_anterior, mes_atual)` retornando `LeituraImpactoIpca` (data-model.md), sem LLM (FR-009)
- [x] T009 [US2] Integrar `leitura_impacto.py` (T008) à montagem da mensagem em `src/ipca/fluxo.py` (T005)

**Checkpoint**: Notificação completa (número + leitura de impacto) na mesma mensagem, conforme FR-003/SC-003.

---

## Phase 5: User Story 3 - Ser avisado se o fluxo parar de funcionar (Priority: P3)

**Goal**: Falha isolada deste fluxo, notificada ao bot dedicado, sem afetar os outros dois fluxos.

**Independent Test**: Forçar exceção na checagem e verificar aviso de falha ao bot IPCA, `estado.json` inalterado, outros fluxos não afetados.

### Tests for User Story 3

- [x] T010 [P] [US3] Teste de integração de falha isolada em `tests/integration/test_fluxo_ipca.py`: exceção durante checagem → `estado.json` inalterado; `_executar_isolado` captura a exceção sem propagar

### Implementation for User Story 3

- [x] T011 [US3] Envolver a chamada ao fluxo IPCA em `src/main.py` com `_executar_isolado`, passando `IPCA_TELEGRAM_BOT_TOKEN`/`IPCA_TELEGRAM_CHAT_ID` para `notificar_falha` (reaproveita o mesmo padrão do fluxo Focus)

**Checkpoint**: Todas as três user stories do fluxo IPCA funcionam de forma independente e isolada.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T012 [P] Adicionar `IPCA_TELEGRAM_BOT_TOKEN`/`IPCA_TELEGRAM_CHAT_ID` ao workflow único do GitHub Actions (`.github/workflows/monitor.yml`, consolidado com o fluxo Focus — um workflow único chama `src/main.py`, que já isola os dois fluxos entre si; dois workflows separados chamando `src/main.py` duplicariam a execução de ambos os fluxos)
- [x] T013 Rodar os cenários de `quickstart.md` (via suíte automatizada, mesmo padrão do fluxo Focus)
- [ ] T014 Rodar o cenário 5 de `quickstart.md` (chamada real à série 433) — pendente de ambiente com acesso de rede real
- [x] T015 [P] Revisar logs/mensagens de erro deste fluxo para confirmar que nenhum token aparece em texto plano (já coberto por `_url_sanitizada`, criada no fluxo Focus — confirmar que se aplica aqui também, já que reaproveita `src/comum/http_retry.py`)

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: sem dependências
- **Foundational (Phase 2)**: nada bloqueante, já existe do fluxo 001
- **User Story 1 (Phase 3)**: depende da Foundational (i.e., de `src/comum/` já existir) — é o MVP
- **User Story 2 (Phase 4)**: depende da User Story 1 (estende `fluxo.py`)
- **User Story 3 (Phase 5)**: depende da User Story 1 (`fluxo.py`) e reaproveita `_executar_isolado`/`notificar_falha` do fluxo 001; independente da User Story 2
- **Polish (Phase 6)**: depende de todas as user stories desejadas

### Parallel Opportunities

- T002/T003 podem rodar em paralelo (arquivos diferentes)
- T007 é independente de T002-T006 (não depende do contrato real)

---

## Implementation Strategy

### MVP First (User Story 1)

1. Completar Setup (T001)
2. Completar Phase 3 (User Story 1)
3. Validar com `quickstart.md` cenários 1–3
4. Deploy do MVP já é possível após User Story 1 (sem leitura de impacto ainda)

### Incremental Delivery

1. User Story 1 → MVP pronto para deploy
2. User Story 2 → leitura de impacto adicionada
3. User Story 3 → resiliência a falhas
4. Polish → workflow de produção

## Notes

- [P] tasks = arquivos diferentes, sem dependência
- Um commit por tarefa (`T0XX: <resumo>`), conforme Princípio I
- T004 (contrato real da série 433) foi obtida em 2026-07-03 antes de
  qualquer código de `src/ipca/cliente_sgs.py`, conforme Princípio II
