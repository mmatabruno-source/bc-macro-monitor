# Data Model: Notificação da Publicação do Relatório de Política Monetária

> Mapeamento confirmado contra o contrato real em
> `contracts/relatorio-dataset.md` (verificado em 2026-07-03).

## Entidade: RelatorioPoliticaMonetaria

| Campo | Tipo | Campo real da API (`sitebcb/rpm/relatorios`) | Descrição | Regras |
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

Resultado da chamada à Claude API com o PDF anexado, contendo os dois
textos usados nas mensagens 2–3 da sequência de notificação. Cada texto
já vem formatado em tópicos curtos, cada um começando com o emoji "▪️"
(pedido do usuário: visão crítica e direta, sem parágrafos longos):

| Campo | Tipo | Descrição |
|---|---|---|
| `visao_cidadao` | string | Tópicos sobre o que é relevante um cidadão saber, com visão crítica, a partir do relatório |
| `visao_investidor` | string | Tópicos sobre o que o relatório estimula ou desestimula um investidor pessoa física a fazer |

## Entidade: SequenciaNotificacaoRelatorio

Conjunto ordenado de mensagens enviadas ao bot dedicado a este fluxo:

1. Aviso de publicação (link `linkPaginaBC` — sempre enviado, mesmo se as
   demais falharem, FR-006)
2. Visão crítica para o cidadão (`AnaliseCritica.visao_cidadao`)
3. Visão do investidor (`AnaliseCritica.visao_investidor`)

Se a chamada à Claude API falhar (ex.: PDF muito grande, erro de rede,
chave inválida), apenas a mensagem 1 é enviada, e a falha é tratada como
falha isolada deste fluxo (User Story 3), sem impedir os outros fluxos.
