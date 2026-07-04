# Implementation Plan: Resumo Semanal do Focus (IPCA, Selic, Câmbio, PIB Total)

**Branch**: `004-focus-resumo-semanal` | **Date**: 2026-07-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-focus-resumo-semanal/spec.md`

## Summary

Checagem periódica (reaproveitando o mesmo cron do `monitor.yml`) da API
`ExpectativasMercadoAnuais` para 4 indicadores (IPCA, Selic, Câmbio, PIB
Total) e 5 anos (corrente + 4 seguintes). Ao detectar uma `Data` de
divulgação mais recente que a última registrada no histórico deste fluxo,
monta e envia uma mensagem única com os 20 valores (4×5), indicando a
direção (subiu/desceu/manteve) contra o valor anterior guardado no
histórico próprio — sem contador de sequência. Estado só é atualizado após
confirmação de envio bem-sucedido; falhas são isoladas deste fluxo.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: `requests` — nenhuma dependência nova (reaproveita `src/comum/`).

**Storage**: `estado.json` (nova chave `ultimo_resumo_focus`) + `historico/focus_resumo/`.

**Testing**: `pytest`. Testes de contrato usam a fixture real já salva em `tests/fixtures/expectativas_anuais_2026-06-26.json`.

**Target Platform**: GitHub Actions (`ubuntu-latest`), mesmo workflow `monitor.yml`.

**Project Type**: Script/CLI simples (single project), reaproveitando `src/comum/`.

**Performance Goals**: N/A — lote único por execução agendada.

**Constraints**: Custo zero; idempotente; nenhum segredo em texto plano; falha deste fluxo não pode impedir os outros 3 fluxos na mesma run.

**Scale/Scope**: 4 indicadores × 5 anos = 20 valores por mensagem; escala trivial.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Princípio I**: ✅ este plano só existe porque spec.md já foi criado antes dele.
- **Princípio II (Nunca codificar contra contrato não verificado)**: ✅
  Resolvido — payload real de `ExpectativasMercadoAnuais` já fornecido
  pelo usuário nesta mesma conversa. Schema documentado em
  `contracts/expectativas-anuais.md`.
- **Princípio III (Isolamento entre fluxos)**: ✅ chave de estado
  (`ultimo_resumo_focus`) e diretório de histórico
  (`historico/focus_resumo/`) próprios, distintos da chave
  `ultima_expectativa_copom` do fluxo 001; processamento envolvido por
  `_executar_isolado`.
- **Princípio IV (Bot dedicado)**: ✅ reaproveita `FOCUS_TELEGRAM_BOT_TOKEN`/
  `FOCUS_TELEGRAM_CHAT_ID` do fluxo 001 (mesmo domínio temático "Focus",
  por decisão do usuário) — não é um bot novo, mas ainda assim um
  destino de notificação explícito, sem fallback compartilhado com outros
  fluxos (Relatório/IPCA continuam com bots próprios).
- **Princípio V (Idempotência)**: ✅ FR-007/FR-008 exigem gravação de
  estado somente após confirmação de envio, por `Data` de divulgação.
- **Princípio VI (API oficial como fonte de verdade)**: ✅ Data mais
  recente e valores sempre vêm da API na execução; anos considerados
  (corrente + 4) calculados a partir da data de execução, não de uma
  lista fixa.
- **Princípio VII (Simplicidade)**: ✅ sem dependência nova; reaproveita
  toda a infraestrutura comum já validada nos fluxos 001/002/003.
- **Princípio VIII (Resiliência)**: ✅ reaproveita `src/comum/http_retry.py`
  (incluindo a correção de encoding `%20` vs `+` do fluxo 001) e
  `src/comum/telegram.py`.
- **Princípio IX (Segredos via GitHub Secrets)**: ✅ nenhum segredo novo —
  reaproveita os secrets já existentes do fluxo Focus.

**Resultado do gate**: PASS. Nenhuma violação identificada.

## Project Structure

### Documentation (this feature)

```text
specs/004-focus-resumo-semanal/
├── plan.md              # Este arquivo
├── research.md          # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── contracts/            # Já resolvido (expectativas-anuais.md)
└── tasks.md              # Phase 2 output (/speckit-tasks - ainda não criado)
```

### Source Code (repository root)

```text
src/
├── focus_resumo/
│   ├── __init__.py
│   ├── cliente_expectativas_anuais.py   # Cliente HTTP de ExpectativasMercadoAnuais
│   ├── comparador.py                     # Direção vs. histórico próprio (sem contador)
│   └── fluxo.py                          # Orquestração: checar -> comparar -> montar mensagem -> notificar -> gravar estado
├── comum/                                 # Já existe — reaproveitado sem alterações
└── main.py                                # Já existe — adiciona chamada ao fluxo via _executar_isolado

tests/
├── contract/
│   └── test_contrato_focus_resumo.py     # Usa a fixture real já salva
├── integration/
│   └── test_fluxo_focus_resumo.py        # Com API mockada a partir da fixture
└── unit/
    └── test_comparador_resumo.py         # Direção subiu/desceu/manteve/sem-historico

estado.json                    # Nova chave ultimo_resumo_focus
historico/
└── focus_resumo/              # Um registro por divulgação processada
```

**Structure Decision**: Projeto único, reaproveitando `src/comum/`.
`src/focus_resumo/` é o único código novo — nome de pacote distinto de
`src/focus/` (fluxo 001) para deixar claro que são fluxos independentes
que só compartilham o bot de destino.

## Complexity Tracking

*Nenhuma violação de constituição a justificar.*
