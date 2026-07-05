# Contrato: Dataset de Relatórios de Política Monetária

**Status**: ✅ Verificado por chamada de teste real em 2026-07-03.
**Atualização (2026-07-05)**: endpoint corrigido de `ri/relatorios` para
`rpm/relatorios` — ver "Correção: renomeação do relatório" abaixo.

## Endpoint

```
GET https://www.bcb.gov.br/api/servico/sitebcb/rpm/relatorios?quantidade=N
```

## Correção: renomeação do relatório (2026-07-05)

O documento foi renomeado de "Relatório de Inflação" para "Relatório de
Política Monetária" (RPM) a partir da edição de mar/2025 (202503). O
endpoint original deste contrato (`ri/relatorios`) é especificamente o
dataset do nome antigo e **parou de receber itens novos** — ficou
travado em `202412` (dez/2024, a última edição sob o nome antigo).

Isso só foi percebido em produção: o fluxo continuava "avisando" sobre o
relatório de dez/2024 mesmo meses depois, porque `identificador` (chave
de idempotência) nunca mudava — não era um bug de comparação, era a
fonte de dados que tinha parado de ser atualizada. Confirmado via
chamada de teste real (`https://www.bcb.gov.br/publicacoes/rpm`, que
lista os RPMs mais recentes) e testando o endpoint irmão
`rpm/relatorios`, que respondeu com o item correto (`202606`,
referência 2026-06-25) e o mesmo schema do dataset antigo — só o
segmento `ri` → `rpm` na URL muda.

## Payload real observado (`quantidade=5`, endpoint `rpm/relatorios`)

```json
{"conteudo":[{"url":"https://www.bcb.gov.br/content/ri/relatorioinflacao/202606/rpm202606p.pdf","linkPaginaBC":"https://www.bcb.gov.br/publicacoes/rpm/202606","identificador":"202606","dataReferencia":"2026-06-25","issn":"ISSN 1517-6576","edicao":"2","volume":"2","descricao":"..."}, ...]}
```

## Schema

| Campo | Tipo | Descrição |
|---|---|---|
| `conteudo` | array | Lista de relatórios, do mais recente ao mais antigo (primeiro elemento = mais recente, conforme amostra ordenada 202412 → 202409 → ... → 202312) |
| `conteudo[].identificador` | string (`"YYYYMM"`) | Identificador único do relatório — **usado como chave de idempotência** (FR-002) |
| `conteudo[].dataReferencia` | string (`"YYYY-MM-DD"`) | Data de publicação |
| `conteudo[].url` | string (URL) | Link direto ao PDF do relatório completo |
| `conteudo[].linkPaginaBC` | string (URL) | Link à página do BC sobre esse relatório (usado no aviso de publicação, FR-003a) |
| `conteudo[].edicao` | string | Número da edição no ano |
| `conteudo[].volume` | string | Volume/ano da publicação |
| `conteudo[].descricao` | string | Texto descritivo genérico (idêntico em todos os relatórios, não é específico de conteúdo/projeções) |

## Regra 1 — Conteúdo é exclusivamente PDF (confirmado)

Não há nenhum campo de texto estruturado (seções, projeções, cenário) no
payload — apenas metadados e um link para o PDF completo (`url`). Isso
confirma, por evidência real (e pela própria descrição da página do
dataset), que a análise crítica (User Story 2) precisa necessariamente
processar o conteúdo do PDF.

## Regra 2 — Extração/análise via Claude API com suporte nativo a PDF

**Decisão**: baixar os bytes do PDF a partir de `url` e enviá-los
diretamente como bloco de documento em uma chamada à API da Anthropic
(Claude), sem nenhuma biblioteca de extração de texto de PDF (`pypdf` ou
similar). O modelo lê o PDF nativamente. Isso mantém a mesma simplicidade
de dependências do projeto (Princípio VII) e reaproveita o padrão de
análise via LLM já validado no copom-monitor-pm para Atas, adaptado para
receber um documento em vez de texto puro.

**Novo segredo necessário**: `ANTHROPIC_API_KEY` (GitHub Secret,
compartilhado apenas por este fluxo, não é um "bot" e portanto não
conflita com o Princípio IV de bot dedicado por fluxo).

## Regra 3 — Idempotência

`identificador` (`"YYYYMM"`) é a chave de idempotência (FR-002/FR-005) —
mais simples e mais estável que `dataReferencia`, já que identifica o
relatório diretamente sem depender de parsing de data.

## Fora de escopo / não verificado

- Comportamento de paginação além do que foi testado com `quantidade=5`.
- Códigos de erro HTTP — nenhuma chamada de teste retornou erro.
- Recurso "Calendário de divulgação" (datas futuras agendadas) — não
  verificado; não é necessário para este fluxo, que usa apenas a API de
  relatórios já publicados como fonte de verdade (Princípio VI).

## Evidência (payload bruto, dataset antigo `ri/relatorios`, congelado em 202412)

```json
{"conteudo":[{"url":"https://www.bcb.gov.br/content/ri/relatorioinflacao/202412/ri202412p.pdf","linkPaginaBC":"https://www.bcb.gov.br/publicacoes/ri/202412","identificador":"202412","dataReferencia":"2024-12-19","issn":"ISSN 1517-6576","edicao":"4","volume":"26","descricao":"O relatório de inflação apresenta as diretrizes das políticas adotadas pelo Copom, considerações acerca da evolução recente do cenário econômico e projeções para a inflação. As projeções são apresentadas em cenários com condicionantes para algumas variáveis econômicas. O Copom utiliza um conjunto amplo de modelos e cenários para orientar suas decisões de política monetária. Ao expor alguns desses cenários, o Copom procura dar maior transparência às decisões de política monetária, contribuindo para sua eficácia no controle da inflação, que é seu objetivo precípuo."},{"url":"https://www.bcb.gov.br/content/ri/relatorioinflacao/202409/ri202409p.pdf","linkPaginaBC":"https://www.bcb.gov.br/publicacoes/ri/202409","identificador":"202409","dataReferencia":"2024-09-26","issn":"ISSN 1517-6576","edicao":"3","volume":"26","descricao":"..."},{"url":"https://www.bcb.gov.br/content/ri/relatorioinflacao/202406/ri202406p.pdf","linkPaginaBC":"https://www.bcb.gov.br/publicacoes/ri/202406","identificador":"202406","dataReferencia":"2024-06-27","issn":"ISSN 1517-6576","edicao":"2","volume":"26","descricao":"..."},{"url":"https://www.bcb.gov.br/content/ri/relatorioinflacao/202403/ri202403p.pdf","linkPaginaBC":"https://www.bcb.gov.br/publicacoes/ri/202403","identificador":"202403","dataReferencia":"2024-03-28","issn":"ISSN 1517-6576","edicao":"1","volume":"26","descricao":"..."},{"url":"https://www.bcb.gov.br/content/ri/relatorioinflacao/202312/ri202312p.pdf","linkPaginaBC":"https://www.bcb.gov.br/publicacoes/ri/202312","identificador":"202312","dataReferencia":"2023-12-21","issn":"ISSN 1517-6576","edicao":"4","volume":"25","descricao":"..."}]}
```

## Evidência (payload bruto, dataset atual `rpm/relatorios`, fixture usada nos testes)

```json
{"conteudo":[{"url":"https://www.bcb.gov.br/content/ri/relatorioinflacao/202606/rpm202606p.pdf","linkPaginaBC":"https://www.bcb.gov.br/publicacoes/rpm/202606","identificador":"202606","dataReferencia":"2026-06-25","issn":"ISSN 1517-6576","edicao":"2","volume":"2","descricao":"..."},{"url":"https://www.bcb.gov.br/content/ri/relatorioinflacao/202603/rpm202603p.pdf","linkPaginaBC":"https://www.bcb.gov.br/publicacoes/rpm/202603","identificador":"202603","dataReferencia":"2026-03-26","issn":"ISSN 1517-6576","edicao":"1","volume":"2","descricao":"..."},{"url":"https://www.bcb.gov.br/content/ri/relatorioinflacao/202512/rpm202512p.pdf","linkPaginaBC":"https://www.bcb.gov.br/publicacoes/rpm/202512","identificador":"202512","dataReferencia":"2025-12-18","issn":"ISSN 1517-6576","edicao":"4","volume":"1","descricao":"..."},{"url":"https://www.bcb.gov.br/content/ri/relatorioinflacao/202509/rpm202509p.pdf","linkPaginaBC":"https://www.bcb.gov.br/publicacoes/rpm/202509","identificador":"202509","dataReferencia":"2025-09-25","issn":"ISSN 1517-6576","edicao":"3","volume":"1","descricao":"..."},{"url":"https://www.bcb.gov.br/content/ri/relatorioinflacao/202506/rpm202506p.pdf","linkPaginaBC":"https://www.bcb.gov.br/publicacoes/rpm/202506","identificador":"202506","dataReferencia":"2025-06-26","issn":"ISSN 1517-6576","edicao":"2","volume":"1","descricao":"..."}]}
```
