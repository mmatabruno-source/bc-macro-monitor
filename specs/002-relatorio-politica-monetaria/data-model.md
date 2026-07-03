# Data Model: Notificação da Publicação do Relatório de Política Monetária

> Nomes de campo conceituais (nível de negócio). Nomes reais de campos e a
> abordagem de extração de conteúdo só serão definidos em
> `contracts/relatorio-dataset.md` depois que o payload real for
> verificado e a decisão PDF-vs-estruturado for tomada (Princípio II — ver
> `research.md`, itens R1/R2).

## Entidade: RelatorioPoliticaMonetaria

| Campo | Tipo | Descrição | Regras |
|---|---|---|---|
| `periodo_referencia` | string | Trimestre/período a que o relatório se refere | Usado como chave de idempotência (FR-002/FR-005) |
| `data_publicacao` | date | Data em que o relatório foi publicado | Informativo |
| `link_documento` | string (URL) | Link ao documento oficial | Usado no aviso de publicação (FR-003a) |
| `conteudo` | ? | Conteúdo do relatório para gerar a análise crítica | Formato exato (texto estruturado vs. PDF) depende de R1/R2 |

## Entidade: RegistroEstadoRelatorio (chave `ultimo_relatorio` em `estado.json`)

| Campo | Tipo | Descrição |
|---|---|---|
| `periodo_referencia` | string | Último período processado com sucesso |

## Entidade: SequenciaNotificacaoRelatorio

Conjunto ordenado de mensagens enviadas ao bot dedicado a este fluxo:

1. Aviso de publicação (sempre enviado, mesmo se as demais falharem — FR-006)
2. Cenário macro
3. Projeções oficiais de inflação
4. Implicação para portfólio

O mecanismo de geração dos itens 2–4 depende da decisão de R2/R3 em
`research.md`.
