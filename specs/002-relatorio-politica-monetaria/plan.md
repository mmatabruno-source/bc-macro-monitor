# Implementation Plan: Notificação da Publicação do Relatório de Política Monetária

**Branch**: `002-relatorio-politica-monetaria` | **Date**: 2026-07-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-relatorio-politica-monetaria/spec.md`

## Summary

Checagem periódica (GitHub Actions cron, diária) do dataset oficial de
Relatórios de Política Monetária. Ao detectar um relatório novo (período
ainda não registrado em `estado.json`), o sistema envia uma sequência de
mensagens ao bot dedicado a este fluxo: aviso de publicação com link,
cenário macro, projeções oficiais de inflação, e implicação para
portfólio. Estado só é atualizado após confirmação de envio bem-sucedido
de toda a sequência; falhas são isoladas deste fluxo. O mecanismo exato de
extração/geração da análise crítica (PDF vs. conteúdo estruturado; uso ou
não de LLM) depende do payload real do dataset e é o primeiro ponto de
decisão desta Phase 0.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: `requests` (chamadas HTTP); possivelmente uma
biblioteca de extração de texto de PDF ou um SDK de LLM — **decisão
adiada para depois do payload real** (ver Constitution Check e
research.md).

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
- **Princípio II (Nunca codificar contra contrato não verificado)**: 🔴
  **GATE BLOQUEANTE** — o payload real do dataset
  `relatorios-de-inflacao-publicados` (Portal de Dados Abertos do BCB)
  ainda não foi fornecido pelo usuário. Nenhum cliente HTTP, parser ou
  `contracts/*.md` com formato de campos pode ser escrito até que isso
  aconteça. Além disso, **uma segunda decisão depende do mesmo payload**:
  se o conteúdo do relatório é acessível de forma estruturada (texto/JSON)
  ou apenas como PDF — o usuário instruiu explicitamente que essa decisão
  (biblioteca de parsing de PDF vs. outra abordagem) só pode ser tomada via
  `/speckit-clarify` depois de ver o payload real, nunca assumida. Ver
  Phase 0 (research.md) para o pedido explícito de ambos.
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
- **Princípio VII (Simplicidade)**: ⚠ **Ponto de atenção** — se o conteúdo
  só existir em PDF, a solução mais simples (ex.: extrair texto bruto e
  resumir via LLM) deve ser preferida a um parser de PDF estruturado
  sob medida, mas essa escolha só pode ser feita depois do payload real
  (não é uma violação, é uma decisão pendente de evidência).
- **Princípio VIII (Resiliência)**: ✅ reaproveita `src/comum/http_retry.py`
  e `src/comum/telegram.py` já implementados no fluxo 001; FR-006 exige
  fallback (enviar ao menos o aviso de publicação) se a análise falhar.
- **Princípio IX (Segredos via GitHub Secrets)**: ✅ nenhum segredo
  codificado. Se a análise crítica usar um LLM, uma nova chave de API
  (ex.: `ANTHROPIC_API_KEY`) seria um novo segredo a declarar — também
  pendente da decisão de research.md.

**Resultado do gate**: BLOQUEADO em Princípio II até o usuário fornecer o
payload real do dataset. A decisão PDF-vs-estruturado e o mecanismo de
análise (LLM ou não) ficam para o mesmo momento, via `/speckit-clarify`.

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
│   ├── cliente_dataset.py     # Cliente HTTP do dataset (BLOQUEADO até contrato real)
│   ├── extrator_conteudo.py   # Extração de conteúdo do relatório — abordagem BLOQUEADA até decisão de research.md
│   ├── gerador_analise.py     # Geração das mensagens de análise crítica — mecanismo BLOQUEADO até decisão de research.md
│   └── fluxo.py               # Orquestração: checar -> extrair -> gerar análise -> notificar (sequência) -> gravar estado
├── comum/                      # Já existe (fluxo 001) — reaproveitado sem alterações estruturais
└── main.py                     # Já existe — adiciona chamada ao fluxo Relatório via _executar_isolado

tests/
├── contract/
│   └── test_contrato_relatorio.py   # Só após payload real (Princípio II)
├── integration/
│   └── test_fluxo_relatorio.py      # Com dataset mockado a partir de fixture real
└── unit/
    └── test_fallback_analise.py     # FR-006 (fallback quando análise falha) — independe do contrato real

estado.json                    # Chave ultimo_relatorio (junto às chaves dos outros 2 fluxos)
historico/
└── relatorios/                # Um registro por relatório processado
```

**Structure Decision**: Projeto único, reaproveitando `src/comum/` do
fluxo 001. `src/relatorio/extrator_conteudo.py` e `gerador_analise.py` têm
sua abordagem interna deliberadamente indefinida até a Phase 0 resolver a
questão PDF/LLM com o payload real.

## Complexity Tracking

*Nenhuma violação de constituição a justificar além do bloqueio do
Princípio II (e a decisão dependente de PDF/LLM), tratados como bloqueio
de tarefa, não como violação.*
