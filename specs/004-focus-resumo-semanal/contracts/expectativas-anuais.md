# Contrato: API de Expectativas de Mercado Anuais (ExpectativasMercadoAnuais)

**Status**: ✅ Verificado por chamadas de teste reais em 2026-07-04.

## Endpoint

```
GET https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoAnuais
```

Mesmo serviço `Expectativas` já usado pelo fluxo Focus/Copom (001), mas
coleção diferente — cobre expectativas por ano-calendário, não por reunião
do Copom.

## Payload real observado (`$filter=Data eq '2026-06-26'`)

Retornou dezenas de indicadores (IPCA, Selic, Câmbio, PIB Total, IGP-M,
contas fiscais, balança comercial, etc.), cada um com uma linha por ano
(2026 a 2035, no exemplo) e por `baseCalculo` (0 e 1). Este fluxo usa
apenas 4 indicadores e 5 anos — ver Regras abaixo.

## Schema

| Campo | Tipo | Observações |
|---|---|---|
| `Indicador` | string | Nome do indicador. Para este fluxo: `"IPCA"`, `"Selic"`, `"Câmbio"`, `"PIB Total"` |
| `IndicadorDetalhe` | string \| null | `null` para os 4 indicadores usados aqui (é usado para desagregações, ex.: `"Balança comercial"` + `"Exportações"`) |
| `Data` | string (`"YYYY-MM-DD"`) | Data da divulgação/pesquisa — usada para idempotência (FR-002/FR-008), mesmo padrão do fluxo Focus/Copom |
| `DataReferencia` | string | **Ano** ao qual a expectativa se refere (ex.: `"2026"`), não confundir com o campo homônimo de outras coleções do mesmo serviço |
| `Mediana` | number | Fonte de verdade deste fluxo (mesmo critério do fluxo 001) |
| `Media`, `DesvioPadrao`, `Minimo`, `Maximo` | number | Não usados |
| `numeroRespondentes` | number \| null | Não usado para decisão (histórico antigo pode vir `null`, ver Fora de escopo) |
| `baseCalculo` | int | `0` ou `1` — usar sempre `0` (base mais ampla), mesma regra do fluxo 001 |

## Regra 1 — Filtro de indicadores

Consultar com `$filter=Data eq '<data_mais_recente>' and (Indicador eq 'IPCA' or Indicador eq 'Selic' or Indicador eq 'Câmbio' or Indicador eq 'PIB Total') and baseCalculo eq 0`.

## Regra 2 — Seleção de anos

Entre as linhas retornadas para cada indicador, filtrar `DataReferencia`
para o ano corrente da execução e os 4 anos seguintes (5 anos no total).
Anos fora dessa janela (o payload real trouxe até 2035) são descartados.

## Regra 3 — Data mais recente (idempotência)

Mesma abordagem do fluxo 001: primeiro descobrir a `Data` mais recente
disponível (`$orderby=Data desc&$top=1`), depois filtrar por essa `Data`
para pegar todos os indicadores/anos daquela divulgação.

## Regra 4 — Comparação semanal (não vem da API)

O campo `Data` avança quase diariamente (mesmo padrão observado no fluxo
001), não estritamente semanal. A comparação "direção vs. semana
anterior" deste fluxo é feita contra o **último valor registrado no
histórico próprio do fluxo** (por indicador/ano), não contra um cálculo
de "há 1 semana" da API — a API não expõe esse dado pronto.

## Fora de escopo / não verificado

- Amostras antigas do payload mostram `numeroRespondentes: null` em
  registros históricos (2011-2017) — não deve ocorrer para dados atuais,
  mas o cliente não deve quebrar se vier `null` (campo não é usado mesmo).
- Códigos de erro HTTP — nenhuma chamada de teste retornou erro.
- Mesmo cuidado de encoding de URL do fluxo 001 (Princípio da correção de
  T030): usar `%20` em vez de `+` para espaços na query string.

## Evidência

Ver `tests/fixtures/expectativas_anuais_2026-06-26.json` (recorte real dos
4 indicadores/5 anos usados por este fluxo, extraído do payload completo
fornecido pelo usuário em 2026-07-04).
