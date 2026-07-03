# Data Model: Notificação da Publicação do Relatório de Política Monetária

> Mapeamento confirmado contra o contrato real em
> `contracts/relatorio-dataset.md` (verificado em 2026-07-03).

## Entidade: RelatorioPoliticaMonetaria

| Campo | Tipo | Campo real da API (`sitebcb/ri/relatorios`) | Descrição | Regras |
|---|---|---|---|---|
| `identificador` | string (`"YYYYMM"`) | `identificador` | Identificador único do relatório | Chave de idempotência (FR-002/FR-005) |
| `data_publicacao` | date | `dataReferencia` | Data em que o relatório foi publicado | Informativo |
| `link_pdf` | string (URL) | `url` | Link direto ao PDF completo | Baixado e enviado à Claude API para análise (R3) |
| `link_pagina` | string (URL) | `linkPaginaBC` | Link à página do BC sobre o relatório | Usado no aviso de publicação (FR-003) |

## Entidade: RegistroEstadoRelatorio (chave `ultimo_relatorio` em `estado.json`)

| Campo | Tipo | Descrição |
|---|---|---|
| `identificador` | string | Último relatório processado com sucesso |

## Entidade: AnaliseCritica

Resultado da chamada à Claude API com o PDF anexado, contendo os três
textos usados nas mensagens 2–4 da sequência de notificação:

| Campo | Tipo | Descrição |
|---|---|---|
| `cenario_macro` | string | Texto sobre o cenário macroeconômico descrito no relatório |
| `projecoes_inflacao` | string | Texto sobre as projeções oficiais de inflação |
| `implicacao_portfolio` | string | Leitura de implicação para decisões de portfólio |

## Entidade: SequenciaNotificacaoRelatorio

Conjunto ordenado de mensagens enviadas ao bot dedicado a este fluxo:

1. Aviso de publicação (link `linkPaginaBC` — sempre enviado, mesmo se as
   demais falharem, FR-006)
2. Cenário macro (`AnaliseCritica.cenario_macro`)
3. Projeções oficiais de inflação (`AnaliseCritica.projecoes_inflacao`)
4. Implicação para portfólio (`AnaliseCritica.implicacao_portfolio`)

Se a chamada à Claude API falhar (ex.: PDF muito grande, erro de rede,
chave inválida), apenas a mensagem 1 é enviada, e a falha é tratada como
falha isolada deste fluxo (User Story 3), sem impedir os outros fluxos.
