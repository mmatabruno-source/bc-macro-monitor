# Implementation Plan: Notificação da Divulgação Mensal do IPCA

**Branch**: `003-ipca-mensal` | **Date**: 2026-07-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-ipca-mensal/spec.md`

## Summary

Checagem periódica (GitHub Actions cron) da série 433 do SGS (IPCA
mensal). Ao detectar um mês de referência ainda não registrado em
`estado.json`, o sistema envia uma notificação única ao bot dedicado a
este fluxo com o número objetivo e uma leitura de impacto para portfólio
gerada por regra determinística (sem LLM, por decisão de
`/speckit-clarify`). Estado só é atualizado após confirmação de envio
bem-sucedido; falhas são isoladas deste fluxo.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: `requests`, biblioteca padrão — sem frameworks
adicionais (Princípio VII).

**Storage**: `estado.json` (chave `ultimo_ipca`) + `historico/ipca/`.

**Testing**: `pytest`. Testes de contrato só depois do payload real
(Princípio II); testes unitários da regra de leitura de impacto
(comparação com mês anterior e com o centro da meta) independem do
contrato.

**Target Platform**: GitHub Actions (`ubuntu-latest`), cron diário.

**Project Type**: Script/CLI simples (single project), reaproveitando
`src/comum/` já construído no fluxo 001.

**Performance Goals**: N/A — lote único por execução agendada.

**Constraints**: Custo zero; idempotente; nenhum segredo em texto plano;
falha deste fluxo não pode impedir os outros dois fluxos na mesma run.

**Scale/Scope**: Um único fluxo, uma divulgação mensal — escala trivial.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Princípio I**: ✅ este plano só existe porque spec.md já foi criado e
  clarificado antes dele.
- **Princípio II (Nunca codificar contra contrato não verificado)**: ✅
  Resolvido em 2026-07-03 — payload real de
  `bcdata.sgs.433/dados/ultimos/3` fornecido pelo usuário. Schema
  documentado em `contracts/ipca-sgs.md`.
- **Princípio III (Isolamento entre fluxos)**: ✅ chave de estado
  (`ultimo_ipca`) e diretório de histórico (`historico/ipca/`) próprios;
  processamento envolvido por `_executar_isolado` (já implementado no
  fluxo 001, reaproveitado aqui).
- **Princípio IV (Bot dedicado)**: ✅ `IPCA_TELEGRAM_BOT_TOKEN` /
  `IPCA_TELEGRAM_CHAT_ID`, próprios deste fluxo.
- **Princípio V (Idempotência)**: ✅ FR-004/FR-005 exigem gravação de
  estado somente após confirmação de envio, por mês de referência.
- **Princípio VI (API oficial como fonte de verdade)**: ✅ o mês de
  referência mais recente vem sempre da série consultada na execução.
  Único ponto de atenção: o centro da meta de inflação (usado na leitura
  de impacto) é um parâmetro de política raramente alterado — tratado como
  constante revisada manualmente uma vez por ano, não como violação deste
  princípio (documentado como Assumption na spec, não decide se o fluxo
  verifica a série).
- **Princípio VII (Simplicidade)**: ✅ sem fila/worker/banco externo; a
  leitura de impacto é uma regra determinística simples (sem LLM),
  reduzindo ainda mais a complexidade em relação aos outros dois fluxos.
- **Princípio VIII (Resiliência)**: ✅ reaproveita `src/comum/http_retry.py`
  e `src/comum/telegram.py` já implementados no fluxo 001.
- **Princípio IX (Segredos via GitHub Secrets)**: ✅ nenhum segredo
  codificado; token/chat_id deste fluxo vêm de variáveis de ambiente.

**Resultado do gate**: PASS. Nenhuma violação identificada.

## Project Structure

### Documentation (this feature)

```text
specs/003-ipca-mensal/
├── plan.md              # Este arquivo
├── research.md          # Phase 0 output (pedido de payload real)
├── data-model.md         # Phase 1 output (conceitual, sem nomes de campo reais)
├── quickstart.md         # Phase 1 output
├── contracts/            # Phase 1 output (placeholder até payload real)
└── tasks.md              # Phase 2 output (/speckit-tasks - ainda não criado)
```

### Source Code (repository root)

```text
src/
├── ipca/
│   ├── __init__.py
│   ├── cliente_sgs.py        # Cliente HTTP da série 433 (BLOQUEADO até contrato real)
│   ├── leitura_impacto.py    # Regra determinística de leitura de impacto (não depende do contrato)
│   └── fluxo.py              # Orquestração: checar -> montar leitura -> notificar -> gravar estado
├── comum/                     # Já existe (criado no fluxo 001) — reaproveitado sem alterações estruturais
└── main.py                    # Já existe — adiciona chamada ao fluxo IPCA via _executar_isolado

tests/
├── contract/
│   └── test_contrato_ipca.py     # Só após payload real (Princípio II)
├── integration/
│   └── test_fluxo_ipca.py        # Com API mockada a partir de fixture real
└── unit/
    └── test_leitura_impacto.py   # Independe do contrato real

estado.json                    # Chave ultimo_ipca (junto às chaves dos outros 2 fluxos)
historico/
└── ipca/                      # Um registro por mês processado
```

**Structure Decision**: Projeto único, reaproveitando a infraestrutura
`src/comum/` já construída no fluxo 001. Apenas `src/ipca/` é novo.

## Complexity Tracking

*Nenhuma violação de constituição a justificar além do bloqueio do
Princípio II, que é tratado como bloqueio de tarefa, não como violação.*
