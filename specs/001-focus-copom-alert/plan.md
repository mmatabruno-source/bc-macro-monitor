# Implementation Plan: Alerta de Mudança Relevante no Focus para a Próxima Reunião do Copom

**Branch**: `001-focus-copom-alert` | **Date**: 2026-07-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-focus-copom-alert/spec.md`

## Summary

Checagem periódica (GitHub Actions cron) da mediana das expectativas de
mercado (Focus) do Banco Central para a Selic na próxima reunião do Copom.
A cada divulgação nova (identificada por sua data de referência), o sistema
compara com a última divulgação registrada em `estado.json` e envia uma
notificação ao bot do Telegram dedicado a este fluxo com o comparativo
subiu/desceu/manteve. O estado só é atualizado após confirmação de envio
bem-sucedido. Falhas são isoladas deste fluxo e não afetam os outros dois
fluxos do repositório.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: `requests` (chamadas HTTP), biblioteca padrão
(`json`, `logging`, `datetime`) — sem frameworks adicionais, por Princípio
VII (Simplicidade) da constituição.

**Storage**: Arquivo `estado.json` no repositório (chave
`ultima_expectativa_copom`) + histórico em `historico/focus/` (um arquivo
Markdown ou JSON por divulgação processada), conforme Princípio III.

**Testing**: `pytest`, com testes de contrato (`tests/contract/`) que só
podem ser escritos depois que o contrato real da API for verificado
(Princípio II), e testes unitários para a lógica de comparação
(subiu/desceu/manteve) e de idempotência, que independem do formato exato
do payload.

**Target Platform**: GitHub Actions (`ubuntu-latest`), execução agendada via
cron; sem servidor dedicado.

**Project Type**: Script/CLI simples (single project), sem frontend nem
serviço de longa duração.

**Performance Goals**: N/A — execução em lote única por vez agendada,
sem requisito de latência além de completar dentro do timeout padrão do
GitHub Actions.

**Constraints**: Custo zero (apenas tiers gratuitos); execução idempotente;
nenhum segredo em texto plano; falha deste fluxo não pode impedir a
execução dos outros dois fluxos do repositório na mesma run.

**Scale/Scope**: Um único fluxo, checagem tipicamente diária, uma
divulgação Focus por semana no cenário normal — escala trivial, sem
necessidade de otimização.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Princípio I (Spec-Driven, sem exceções)**: ✅ este plano só existe porque
  spec.md já foi criado, validado e clarificado antes dele.
- **Princípio II (Nunca codificar contra contrato não verificado)**: ✅
  Resolvido em 2026-07-03 — o payload real do endpoint
  `ExpectativasMercadoSelic` (Olinda) foi fornecido pelo usuário via 4
  chamadas de teste reais (service document, `$metadata`, filtro por
  `Reuniao`, filtro por `Data`). `contracts/focus-api.md` documenta o
  schema completo e as regras de seleção (`baseCalculo`, identificação da
  próxima reunião) a partir desses payloads reais, sem nenhuma suposição.
- **Princípio III (Isolamento entre fluxos)**: ✅ este fluxo usa sua própria
  chave de estado (`ultima_expectativa_copom`) e diretório de histórico
  (`historico/focus/`), e seu processamento MUST ser envolvido pelo mesmo
  padrão de isolamento de execução (`_executar_isolado`) usado pelos outros
  dois fluxos no ponto de entrada comum do repositório.
- **Princípio IV (Bot dedicado, sem bot padrão)**: ✅ token e chat_id deste
  fluxo são parâmetros próprios (`FOCUS_TELEGRAM_BOT_TOKEN`,
  `FOCUS_TELEGRAM_CHAT_ID`), nunca compartilhados com os outros fluxos.
- **Princípio V (Idempotência)**: ✅ FR-006/FR-007 do spec já exigem que o
  estado só seja gravado após confirmação de envio bem-sucedido, por
  divulgação (data de referência), não apenas por valor.
- **Princípio VI (API oficial como fonte de verdade)**: ✅ a próxima reunião
  e sua expectativa vêm sempre da API consultada na execução, nunca de uma
  lista de datas fixa no repositório.
- **Princípio VII (Simplicidade)**: ✅ sem fila, worker ou banco externo;
  apenas script Python + JSON/Markdown versionados.
- **Princípio VIII (Resiliência)**: ✅ reaproveita `_retentavel`,
  `_espera_para_tentativa`, `_sanitizar` e o fallback de formatação Markdown
  do projeto irmão, adaptando `enviar_mensagem(texto, token, chat_id)` para
  receber o token/chat_id deste fluxo.
- **Princípio IX (Segredos via GitHub Secrets)**: ✅ nenhum segredo é
  codificado; token e chat_id do bot deste fluxo vêm de variáveis de
  ambiente injetadas pelo workflow a partir de GitHub Secrets.

**Resultado do gate**: PASS condicional — todos os princípios são
satisfeitos pelo desenho deste plano, exceto que a implementação do cliente
HTTP/parser real fica formalmente bloqueada pelo Princípio II até o usuário
fornecer o payload de teste. Isso é tratado como bloqueio de tarefa, não
como violação a justificar em Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-focus-copom-alert/
├── plan.md              # Este arquivo
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (parcial — ver bloqueio do Princípio II)
└── tasks.md             # Phase 2 output (/speckit-tasks - ainda não criado)
```

### Source Code (repository root)

```text
src/
├── focus/
│   ├── __init__.py
│   ├── cliente_expectativas.py   # Cliente HTTP do endpoint Focus (BLOQUEADO até contrato real)
│   ├── comparador.py             # Lógica de subiu/desceu/manteve e detecção de nova divulgação
│   └── fluxo.py                  # Orquestração do fluxo: checar -> comparar -> notificar -> gravar estado
├── comum/
│   ├── __init__.py
│   ├── http_retry.py             # _retentavel / _espera_para_tentativa (compartilhado entre os 3 fluxos)
│   ├── telegram.py                # enviar_mensagem(texto, token, chat_id) + fallback de formatação + _sanitizar
│   ├── estado.py                  # leitura/escrita de estado.json (chaves por fluxo)
│   └── isolamento.py              # _executar_isolado (compartilhado entre os 3 fluxos)
└── main.py                        # Ponto de entrada único do GitHub Actions; chama os 3 fluxos isoladamente

tests/
├── contract/
│   └── test_contrato_focus.py    # Só pode ser escrito após o payload real ser fornecido (Princípio II)
├── integration/
│   └── test_fluxo_focus.py       # Fluxo completo com API mockada a partir do payload real
└── unit/
    ├── test_comparador.py
    └── test_estado.py

estado.json                        # Chave ultima_expectativa_copom (e chaves dos outros 2 fluxos)
historico/
└── focus/                         # Um registro por divulgação processada
```

**Structure Decision**: Projeto único (Option 1 — single project), sem
frontend/backend separados. `src/comum/` concentra os padrões de
resiliência reaproveitados do copom-monitor-pm e compartilhados pelos três
fluxos deste repositório; `src/focus/` contém apenas a lógica específica
deste fluxo. `src/main.py` é o único ponto de entrada do cron, chamando
cada fluxo através de `_executar_isolado` (Princípio III).

## Complexity Tracking

*Nenhuma violação de constituição a justificar — seção não aplicável.*
