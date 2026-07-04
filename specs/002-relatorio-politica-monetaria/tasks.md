---

description: "Task list for feature 002-relatorio-politica-monetaria"
---

# Tasks: Notificação da Publicação do Relatório de Política Monetária

**Input**: Design documents from `/specs/002-relatorio-politica-monetaria/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Incluídos — idempotência e o fallback FR-006 justificam testes desde já.

**Organization**: Tarefas agrupadas por user story (US1, US2, US3), com Setup, Foundational (mínima, reaproveita `src/comum/` do fluxo 001) e Polish.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependência)
- **[Story]**: US1, US2 ou US3 (ver spec.md)

## Path Conventions

Projeto único: `src/relatorio/` (novo), `src/comum/` (reaproveitado), `tests/`, `historico/relatorios/`.

## Phase 1: Setup

- [x] T001 Criar diretório `historico/relatorios/` (com `.gitkeep`)
- [x] T002 [P] Adicionar `anthropic` ao `requirements.txt` (já feito) e instalar

**Checkpoint**: `src/comum/` já existe do fluxo 001 — nenhuma infraestrutura nova bloqueante.

---

## Phase 2: Foundational

**Purpose**: Nenhuma infraestrutura nova bloqueante além do SDK `anthropic` — `http_retry.py`, `telegram.py`, `estado.py`, `isolamento.py` já existem e são reaproveitados sem alteração estrutural.

**Checkpoint**: Nada a fazer nesta fase além de confirmar que os módulos comuns já existem.

---

## Phase 3: User Story 1 - Ser avisado assim que um novo relatório é publicado (Priority: P1) 🎯 MVP

**Goal**: Detectar um relatório novo (via `identificador`) e enviar ao menos o aviso de publicação com link, de forma idempotente.

**Independent Test**: Simular duas checagens consecutivas do dataset (uma sem o relatório novo, outra com ele) e verificar que a notificação só ocorre quando há relatório novo, e que reler o mesmo relatório não gera notificação duplicada.

### Tests for User Story 1

- [x] T003 [P] [US1] Contract test do parser do dataset em `tests/contract/test_contrato_relatorio.py`, usando `tests/fixtures/relatorios_quantidade_5.json` e as regras de `contracts/relatorio-dataset.md`
- [x] T004 [P] [US1] Teste de integração do aviso de publicação (sem análise) em `tests/integration/test_fluxo_relatorio.py`, com dataset mockado a partir da fixture

### Implementation for User Story 1

- [x] T005 [US1] Implementar `src/relatorio/cliente_dataset.py`: cliente HTTP para `sitebcb/ri/relatorios?quantidade=N` (usa `src/comum/http_retry.py`), retornando o `RelatorioPoliticaMonetaria` mais recente (primeiro elemento de `conteudo`)
- [x] T006 [US1] Implementar `src/relatorio/fluxo.py` (esqueleto): checagem (T005) → verificação de idempotência por `identificador` → envio do aviso de publicação (`linkPaginaBC`) → gravação de estado (chave `ultimo_relatorio`) SOMENTE após confirmação de envio bem-sucedido
- [x] T007 [US1] Implementar gravação de histórico em `historico/relatorios/<identificador>.json` a cada relatório processado com sucesso

**Checkpoint**: User Story 1 completa — MVP do fluxo Relatório (aviso + link, sem análise ainda).

---

## Phase 4: User Story 2 - Receber análise crítica orientada a portfólio (Priority: P2)

**Goal**: Baixar o PDF do relatório e gerar, via Claude API (documento nativo), as mensagens de cenário macro, projeções e implicação para portfólio — com fallback para apenas o aviso se a análise falhar.

**Independent Test**: Fornecer um PDF de teste (ou mock da resposta da Claude API) e verificar que a sequência de 4 mensagens é enviada corretamente; forçar falha na análise e verificar que apenas a mensagem 1 é enviada.

### Tests for User Story 2

- [x] T008 [P] [US2] Teste unitário de `gerador_analise.py` em `tests/unit/test_gerador_analise.py`, mockando a chamada à Claude API e verificando que `AnaliseCritica` é montada a partir da resposta
- [x] T009 [P] [US2] Teste de integração da sequência completa de 4 mensagens em `tests/integration/test_fluxo_relatorio.py` (mesma suíte de T004), com Claude API mockada com sucesso
- [x] T010 [P] [US2] Teste unitário do fallback (FR-006) em `tests/unit/test_fallback_analise.py`: análise falha → apenas mensagem de aviso é enviada, sem interromper o fluxo

### Implementation for User Story 2

- [x] T011 [US2] Implementar `src/relatorio/gerador_analise.py`: baixa os bytes do PDF (`requests`, via `src/comum/http_retry.py`) a partir de `url`, monta uma chamada à Claude API (`anthropic`) com o PDF como bloco de documento, prompt pedindo cenário macro / projeções / implicação para portfólio como 3 seções distintas, e retorna `AnaliseCritica`
- [x] T012 [US2] Estender `src/relatorio/fluxo.py` (T006): após o aviso de publicação, tentar gerar a análise (T011); se bem-sucedida, enviar as 3 mensagens adicionais na ordem definida em `data-model.md`; se falhar, capturar a exceção, logar e seguir sem interromper (o relatório já é considerado processado pelo aviso enviado com sucesso)

**Checkpoint**: Notificação completa (4 mensagens) quando a análise funciona; fallback gracioso quando não funciona.

---

## Phase 5: User Story 3 - Ser avisado se o fluxo parar de funcionar (Priority: P3)

**Goal**: Falha isolada deste fluxo (ex.: dataset indisponível), notificada ao bot dedicado, sem afetar os outros dois fluxos.

**Independent Test**: Forçar exceção na checagem do dataset (não na análise, que já tem fallback próprio) e verificar aviso de falha ao bot Relatório, `estado.json` inalterado, outros fluxos não afetados.

### Tests for User Story 3

- [x] T013 [P] [US3] Teste de integração de falha isolada em `tests/integration/test_fluxo_relatorio.py`: exceção durante a checagem do dataset → `estado.json` inalterado; `_executar_isolado` captura sem propagar

### Implementation for User Story 3

- [x] T014 [US3] Envolver a chamada ao fluxo Relatório em `src/main.py` com `_executar_isolado`, passando `RELATORIO_TELEGRAM_BOT_TOKEN`/`RELATORIO_TELEGRAM_CHAT_ID` para `notificar_falha` (reaproveita o mesmo padrão dos fluxos Focus/IPCA)

**Checkpoint**: Todas as três user stories do fluxo Relatório funcionam de forma independente e isolada.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T015 [P] Adicionar `RELATORIO_TELEGRAM_BOT_TOKEN`/`RELATORIO_TELEGRAM_CHAT_ID` e `ANTHROPIC_API_KEY` ao workflow único `.github/workflows/monitor.yml`
- [x] T016 Rodar os cenários 1–3 de `quickstart.md` via suíte automatizada
- [ ] T017 Rodar o cenário 4 de `quickstart.md` (chamada real ao dataset + PDF + Claude API). **Parcialmente validada em 2026-07-04**: a chamada ao dataset funcionou em produção (aviso de publicação do relatório 202412 recebido com sucesso, `estado.json` gravado). A parte da análise via Claude API (cenário/projeções/portfólio) ainda não foi validada — `ANTHROPIC_API_KEY` ainda não foi cadastrado como Secret pelo usuário; o fallback (FR-006) está funcionando como esperado nesse meio-tempo (só o aviso é enviado). Reabrir esta tarefa depois que o secret for adicionado.
- [x] T018 [P] Revisar logs/mensagens de erro deste fluxo para confirmar que nenhum token/chave aparece em texto plano (reaproveita `_url_sanitizada`; adicionar sanitização equivalente para `ANTHROPIC_API_KEY` se ela aparecer em alguma URL ou header logado)

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: sem dependências
- **Foundational (Phase 2)**: nada bloqueante, já existe do fluxo 001
- **User Story 1 (Phase 3)**: depende da Foundational — é o MVP (aviso + link, sem análise)
- **User Story 2 (Phase 4)**: depende da User Story 1 (estende `fluxo.py` com a sequência de análise)
- **User Story 3 (Phase 5)**: depende da User Story 1 (`fluxo.py`); independente da User Story 2
- **Polish (Phase 6)**: depende de todas as user stories desejadas

### Parallel Opportunities

- T003/T004 podem rodar em paralelo
- T008/T009/T010 podem rodar em paralelo entre si

---

## Implementation Strategy

### MVP First (User Story 1)

1. Completar Setup (T001-T002)
2. Completar Phase 3 (User Story 1) — aviso + link, sem análise
3. Validar com `quickstart.md` cenários 1–2
4. Deploy do MVP já é possível após User Story 1 (análise vem depois)

### Incremental Delivery

1. User Story 1 → MVP pronto para deploy (aviso + link)
2. User Story 2 → análise crítica via Claude API adicionada
3. User Story 3 → resiliência a falhas
4. Polish → workflow de produção

## Notes

- [P] tasks = arquivos diferentes, sem dependência
- Um commit por tarefa (`T0XX: <resumo>`), conforme Princípio I
- O contrato real do dataset (payload + confirmação PDF-only) e a decisão
  de usar a Claude API com PDF nativo foram obtidos/tomados em
  2026-07-03, antes de qualquer código de `src/relatorio/`, conforme
  Princípio II
