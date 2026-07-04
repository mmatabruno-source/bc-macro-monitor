# bc-macro-monitor

Monitor automático de indicadores macroeconômicos do Banco Central do
Brasil, com alertas via Telegram para apoio a decisões de portfólio.
Projeto irmão do `copom-monitor-pm` (monitor de Comunicados/Atas do
Copom), construído com [GitHub Spec Kit](https://github.com/github/spec-kit)
(Spec-Driven Development) — cada fluxo tem sua spec, plano e tarefas em
`specs/`.

## Fluxos em produção

| # | Fluxo | O que monitora | Cadência | Bot |
|---|---|---|---|---|
| 001 | Focus/Copom | Mediana da Selic (Focus) para a próxima reunião do Copom, com comparação subiu/desceu/manteve | ~diária (a cada nova divulgação) | `@monitor_boletim_focus_bot` |
| 002 | Relatório de Política Monetária | Publicação trimestral do RPM, com análise crítica (cenário macro, projeções, portfólio) via Claude API lendo o PDF nativamente | diária (evento raro, 4x/ano) | `@monitor_politica_monetaria_bot` |
| 003 | IPCA | Divulgação mensal do IPCA, com leitura de impacto por regra determinística (sem LLM) | diária (evento mensal) | `@monitor_ipca_bot` |
| 004 | Resumo Semanal do Focus | IPCA, Selic, Câmbio e PIB Total — valor "hoje" para o ano corrente + 4 seguintes, com direção vs. checagem anterior | a cada nova divulgação (~diária) | `@monitor_boletim_focus_bot` (mesmo do 001) |

Os quatro fluxos rodam na mesma execução agendada
(`.github/workflows/monitor.yml`), isolados entre si — uma falha em um
nunca impede os outros de rodar e notificar.

## Arquitetura

- **Linguagem**: Python 3.12. **Execução**: GitHub Actions (cron diário em
  dias úteis), sem servidor dedicado.
- **Armazenamento**: `estado.json` (uma chave por fluxo) + `historico/`
  (um arquivo por divulgação processada), versionados no próprio
  repositório Git — sem banco de dados externo. O próprio workflow
  commita `estado.json`/`historico/` de volta ao repositório após cada
  execução.
- **Infraestrutura compartilhada** (`src/comum/`): retry HTTP seletivo
  (429/5xx, respeita `Retry-After`, encoding correto de URL OData —
  `%20` em vez de `+`), envio ao Telegram com fallback de formatação e
  sanitização de tokens em log, leitura/escrita de estado por chave,
  isolamento de falha entre fluxos (`_executar_isolado`).
- **Segredos**: tokens dos 3 bots do Telegram + `ANTHROPIC_API_KEY`,
  todos via GitHub Secrets — nunca em texto plano.
- **Idempotência**: nenhuma publicação já processada gera segunda
  notificação; o estado só é gravado depois que o envio for confirmado.
- **Fonte de verdade**: sempre a API oficial correspondente a cada fluxo,
  nunca um calendário estimado.

## Metodologia

Todo código deste repositório passa por
`/speckit-constitution` → `/speckit-specify` → `/speckit-plan` →
`/speckit-tasks` → `/speckit-implement`, nessa ordem — ver
`.specify/memory/constitution.md` para os princípios completos. Nenhum
cliente HTTP é escrito antes de o contrato da API correspondente ser
verificado com um payload real (`contracts/*.md` em cada `specs/NNN-*/`).

## Setup

Cadastrar como GitHub Secrets (Settings → Secrets and variables → Actions):

- `FOCUS_TELEGRAM_BOT_TOKEN` / `FOCUS_TELEGRAM_CHAT_ID`
- `IPCA_TELEGRAM_BOT_TOKEN` / `IPCA_TELEGRAM_CHAT_ID`
- `RELATORIO_TELEGRAM_BOT_TOKEN` / `RELATORIO_TELEGRAM_CHAT_ID`
- `ANTHROPIC_API_KEY` (usado só pelo fluxo 002, para a análise crítica do
  Relatório de Política Monetária)

```bash
pip install -r requirements.txt
python -m pytest tests/ -q   # 64 testes (unit + contract + integration)
python -m src.main            # roda os 4 fluxos localmente
```
