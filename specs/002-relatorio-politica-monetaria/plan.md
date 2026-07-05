# Implementation Plan: Notificação da Publicação do Relatório de Política Monetária

**Branch**: `002-relatorio-politica-monetaria` | **Date**: 2026-07-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-relatorio-politica-monetaria/spec.md`

> **Atualização (2026-07-05, trilha leve)**: dois pontos deste plano ficaram
> desatualizados por ajustes feitos após a implementação inicial, sem
> passar pelo pipeline completo — ver `research.md` para o registro
> completo de cada mudança:
> 1. O endpoint do dataset mudou de `sitebcb/ri/relatorios` para
>    `sitebcb/rpm/relatorios` (o documento foi renomeado de "Relatório de
>    Inflação" para "Relatório de Política Monetária" e o dataset antigo
>    parou de receber itens novos).
> 2. A análise crítica foi reformulada de 3 seções/4 mensagens (cenário
>    macro, projeções de inflação, implicação para portfólio) para 2
>    seções/3 mensagens (visão crítica para o cidadão, visão do
>    investidor pessoa física), por pedido do usuário.
> O restante deste documento (arquitetura, Constitution Check, decisões de
> design) permanece válido.

## Summary

Checagem periódica (GitHub Actions cron, diária) do dataset oficial de
Relatórios de Política Monetária (`sitebcb/rpm/relatorios` — ver nota de
atualização acima). Ao detectar um relatório novo (`identificador` ainda
não registrado em `estado.json`), o sistema baixa o PDF do relatório e o
envia como documento nativo à Claude API para gerar a análise crítica
(visão crítica para o cidadão + visão do investidor pessoa física — ver
nota de atualização acima), então envia uma sequência de mensagens ao bot
dedicado a este fluxo: aviso de publicação com link, seguido das 2
mensagens de análise. Se a análise falhar, ao menos o aviso de publicação
é enviado (FR-006). Estado só é atualizado após confirmação de envio
bem-sucedido; falhas são isoladas deste fluxo.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: `requests` (chamadas HTTP) + `anthropic` (SDK da
Claude API, para análise do PDF anexado nativamente — sem biblioteca de
extração de texto de PDF, ver research.md R3).

**Storage**: `estado.json` (chave `ultimo_relatorio`) + `historico/relatorios/`.

**Testing**: `pytest`. Testes de contrato só depois do payload real.

**Target Platform**: GitHub Actions (`ubuntu-latest`), cron diário.

**Project Type**: Script/CLI simples (single project), reaproveitando
`src/comum/` já construído no fluxo 001.

**Performance Goals**: N/A — lote único por execução agendada.

**Constraints**: Custo zero; idempotente; nenhum segredo em texto plano;
falha deste fluxo não pode impedir os outros dois fluxos na mesma run.

**Scale/Scope**: Um único fluxo, publicação trimestral — escala trivial em
volume, mas a complexidade de extração de conteúdo é a maior incerteza
técnica deste projeto até agora.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Princípio I**: ✅ este plano só existe porque spec.md já foi criado
  antes dele.
- **Princípio II (Nunca codificar contra contrato não verificado)**: ✅
  Resolvido em 2026-07-03 — payload real de
  `sitebcb/ri/relatorios?quantidade=N` fornecido pelo usuário. Confirma
  que o conteúdo é só PDF (sem texto estruturado). Schema documentado em
  `contracts/relatorio-dataset.md`.
- **Princípio III (Isolamento entre fluxos)**: ✅ chave de estado
  (`ultimo_relatorio`) e diretório de histórico (`historico/relatorios/`)
  próprios; processamento envolvido por `_executar_isolado` (reaproveitado
  do fluxo 001).
- **Princípio IV (Bot dedicado)**: ✅ `RELATORIO_TELEGRAM_BOT_TOKEN` /
  `RELATORIO_TELEGRAM_CHAT_ID`, próprios deste fluxo.
- **Princípio V (Idempotência)**: ✅ FR-004/FR-005 exigem gravação de
  estado somente após confirmação de envio de toda a sequência de
  mensagens, por período/trimestre.
- **Princípio VI (API oficial como fonte de verdade)**: ✅ o relatório mais
  recente vem sempre do dataset consultado na execução, nunca de um
  calendário trimestral estimado (FR-009).
- **Princípio VII (Simplicidade)**: ✅ enviar o PDF diretamente à Claude
  API (suporte nativo) evita introduzir uma biblioteca de extração de PDF
  — menos uma dependência do que a alternativa considerada.
- **Princípio VIII (Resiliência)**: ✅ reaproveita `src/comum/http_retry.py`
  e `src/comum/telegram.py` já implementados no fluxo 001; FR-006 exige
  fallback (enviar ao menos o aviso de publicação) se a análise falhar.
- **Princípio IX (Segredos via GitHub Secrets)**: ✅ nenhum segredo
  codificado; nova chave `ANTHROPIC_API_KEY` declarada como GitHub Secret,
  usada apenas por este fluxo.

**Resultado do gate**: PASS. Nenhuma violação identificada.

## Project Structure

### Documentation (this feature)

```text
specs/002-relatorio-politica-monetaria/
├── plan.md              # Este arquivo
├── research.md          # Phase 0 output (pedido de payload real + decisão PDF/LLM pendente)
├── data-model.md         # Phase 1 output (conceitual, sem nomes de campo reais)
├── quickstart.md         # Phase 1 output
├── contracts/            # Phase 1 output (placeholder até payload real)
└── tasks.md              # Phase 2 output (/speckit-tasks - ainda não criado)
```

### Source Code (repository root)

```text
src/
├── relatorio/
│   ├── __init__.py
│   ├── cliente_dataset.py     # Cliente HTTP do dataset de relatórios
│   ├── gerador_analise.py     # Baixa o PDF e chama a Claude API (documento nativo) para gerar AnaliseCritica
│   └── fluxo.py               # Orquestração: checar -> gerar análise -> notificar (sequência, com fallback FR-006) -> gravar estado
├── comum/                      # Já existe (fluxo 001) — reaproveitado sem alterações estruturais
└── main.py                     # Já existe — adiciona chamada ao fluxo Relatório via _executar_isolado

tests/
├── contract/
│   └── test_contrato_relatorio.py   # Usa o payload real verificado (fixture)
├── integration/
│   └── test_fluxo_relatorio.py      # Com dataset e Claude API mockados
└── unit/
    └── test_fallback_analise.py     # FR-006 (fallback quando análise falha)

estado.json                    # Chave ultimo_relatorio (junto às chaves dos outros 2 fluxos)
historico/
└── relatorios/                # Um registro por relatório processado
```

**Structure Decision**: Projeto único, reaproveitando `src/comum/` do
fluxo 001. `src/relatorio/gerador_analise.py` usa a Claude API com o PDF
como documento nativo, sem biblioteca de extração de texto.

## Complexity Tracking

*Nenhuma violação de constituição a justificar.*
