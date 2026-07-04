# Contrato: API de Expectativas de Mercado (Focus) — ExpectativasMercadoSelic

**Status**: ✅ Verificado por chamadas de teste reais em 2026-07-03. Ver
seção "Evidência" para as respostas brutas que fundamentam cada regra.

## Endpoint

```
GET https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoSelic
```

Parâmetros OData usados por este projeto:
- `$filter=Indicador eq 'Selic'` — a coleção parece já ser específica de
  Selic, mas o campo `Indicador` existe no schema e será filtrado
  explicitamente por robustez.
- `$filter=Data eq '<YYYY-MM-DD>'` combinável com o filtro acima via `and`,
  para obter todas as linhas de uma única divulgação.
- `$orderby=Data desc` — para descobrir qual é a divulgação mais recente
  antes de buscar todas as suas linhas.
- `$format=json` — formato de resposta.

## Schema (confirmado via `$metadata`, EntityType `ExpectativaMercadoSelic`)

| Campo | Tipo OData | Observações |
|---|---|---|
| `Indicador` | `Edm.String` | Sempre `"Selic"` nesta coleção |
| `Data` | `Edm.String` | Data de referência da divulgação/pesquisa Focus, formato `"YYYY-MM-DD"` |
| `Reuniao` | `Edm.String` | Identificador da reunião do Copom, formato `"R<n>/<yyyy>"` (ex.: `"R5/2026"`) — **não é uma data**, ver regra de ordenação abaixo |
| `Media` | `Edm.Decimal` | Média das expectativas — NÃO usada por este fluxo (Princípio: mediana é a fonte única, FR-011) |
| `Mediana` | `Edm.Decimal` | **Fonte de verdade única deste fluxo** (FR-011) |
| `DesvioPadrao` | `Edm.Decimal` | Não usado |
| `Minimo` | `Edm.Decimal` | Não usado |
| `Maximo` | `Edm.Decimal` | Não usado |
| `numeroRespondentes` | `Edm.Int32` | Usado apenas para resolver `baseCalculo` (ver regra abaixo) |
| `baseCalculo` | `Edm.Int32` | `0` ou `1` — ver regra de seleção abaixo |

## Regra 1 — Seleção de `baseCalculo`

**Decisão**: usar sempre a linha com `baseCalculo = 0`.

**Evidência empírica** (chamada filtrando por `Reuniao eq 'R4/2028'`,
ordenada por `Data desc`): em todo par de linhas com a mesma `Data` e
`Reuniao`, a linha com `baseCalculo = 0` tem `numeroRespondentes` **igual ou
maior** que a linha com `baseCalculo = 1` (ex.: 2026-06-26: 66 vs. 48;
2026-06-25: 50 vs. 48). Nunca foi observado o contrário. Isso indica que
`baseCalculo = 0` é a base mais ampla (super-conjunto de respondentes) e
`baseCalculo = 1` é um subconjunto (provavelmente respondentes com
atualização recente, mas o nome oficial do critério não foi confirmado por
documentação da própria API — a metadata OData não traz anotação
descritiva para este campo). A decisão de negócio não depende de saber o
nome oficial do critério, apenas de escolher consistentemente a base mais
ampla.

## Regra 2 — Identificação da "próxima reunião do Copom"

**Decisão**: entre todas as linhas retornadas para a divulgação mais
recente (`Data` mais recente), parsear `Reuniao` como `(ano, número)` a
partir do formato `"R<número>/<ano>"`, e escolher a linha com o **menor**
par `(ano, número)`.

**Evidência empírica**: a chamada filtrando por
`Data eq '2026-06-26' and Indicador eq 'Selic'` (sem filtrar por `Reuniao`)
retornou 15 reuniões distintas, de `R5/2026` (a menor) até `R4/2028` (a
maior). Nenhuma reunião anterior a `R5/2026` apareceu — ou seja, a API já
exclui reuniões passadas da divulgação, e a menor `Reuniao` presente é,
por construção, a próxima reunião a partir da data daquela divulgação.
Isso elimina a necessidade de qualquer fonte externa de calendário (Atas,
release de imprensa, ou tabela hardcoded) — resolvendo a tensão com o
Princípio VI da constituição (fonte de verdade é sempre a API).

**Regra de parsing**: `Reuniao` = `"R{numero}/{ano}"` → chave de ordenação
`(int(ano), int(numero))`, menor primeiro.

## Regra 3 — Data de referência da divulgação (idempotência)

O campo `Data` (não confundir com o "ano" dentro de `Reuniao`) é a data de
referência da divulgação/pesquisa Focus, e é o campo usado para
idempotência por divulgação (FR-004a/FR-007): duas leituras com o mesmo
`Data` para a mesma `Reuniao` são a mesma divulgação; um `Data` mais
recente é uma nova divulgação.

## Evidência (payloads reais brutos)

### Chamada 1 — sem filtro, `$top=5&$orderby=Data desc`
```json
{"@odata.context":"https://was-p.bcnet.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata$metadata#ExpectativasMercadoSelic","value":[{"Indicador":"Selic","Data":"2026-06-26","Reuniao":"R4/2028","Media":11.4844,"Mediana":11.5000,"DesvioPadrao":0.9688,"Minimo":9.7500,"Maximo":14.2500,"numeroRespondentes":48,"baseCalculo":1}, ...]}
```
(ver histórico da conversa para o payload completo de 5 linhas)

### Chamada 2 — filtrada por `Reuniao eq 'R4/2028'`, ordenada por `Data desc`
Confirma o padrão de `baseCalculo` (Regra 1) ao longo de várias divulgações
consecutivas para a mesma reunião.

### Chamada 3 — filtrada por `Data eq '2026-06-26' and Indicador eq 'Selic'`
Retornou as 15 reuniões cobertas por essa única divulgação, de `R5/2026`
(menor) a `R4/2028` (maior) — payload completo usado para confirmar a
Regra 2. Arquivo de referência para fixtures de teste:
`tests/fixtures/focus_divulgacao_2026-06-26.json` (a ser criado a partir
deste payload real na implementação).

### Metadata (`$metadata`)
Confirma tipos de campo da Regra de Schema acima; não traz anotações de
documentação para `baseCalculo` (daí a Regra 1 ser resolvida
empiricamente, não por nome oficial do critério).

## Fora de escopo / não verificado

- Comportamento de paginação (`$top`/`$skip`) além do que foi testado.
- Códigos de erro HTTP (nenhuma chamada de teste retornou erro).
- Qualquer relação entre `Reuniao` e a data de calendário exata da reunião
  (não necessária para este fluxo, ver Regra 2).
