# Contrato: Série 433 do SGS (IPCA mensal)

**Status**: ✅ Verificado por chamada de teste real em 2026-07-03.

## Endpoint

```
GET https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados/ultimos/N?formato=json
```

`N` = quantidade de valores mais recentes a retornar.

## Payload real observado (`ultimos/3`)

```json
[{"data":"01/03/2026","valor":"0.88"},{"data":"01/04/2026","valor":"0.67"},{"data":"01/05/2026","valor":"0.58"}]
```

## Schema

| Campo | Tipo | Formato | Observações |
|---|---|---|---|
| `data` | string | `"DD/MM/YYYY"` | Sempre observado com `DD = "01"` nas 3 amostras — representa o mês de referência (não o dia real de divulgação). Mês/ano são as partes relevantes: `mes_referencia = "{YYYY}-{MM}"`. |
| `valor` | string | número decimal com ponto (`"0.88"`) | Variação percentual mensal do IPCA. **Vem como string, não como número** — cliente deve converter com `float(valor)`. |

## Regras de parsing

- `mes_referencia` (chave de idempotência, FR-002) = `data[6:10] + "-" + data[3:5]`
  (extrai `YYYY-MM` de `"01/MM/YYYY"`).
- `variacao_mensal` = `float(valor)`.
- A resposta é uma lista simples (array JSON), ordenada cronologicamente
  (mais antigo primeiro, mais recente por último, conforme a amostra:
  03/2026 → 04/2026 → 05/2026). O mês mais recente é o **último elemento**
  da lista.

## Fora de escopo / não verificado

- Comportamento com `N` grande (paginação, limites) — não testado, não
  necessário para este fluxo (basta `ultimos/2` para comparar mês atual
  com o anterior).
- Códigos de erro HTTP — nenhuma chamada de teste retornou erro.
- Núcleos de inflação (séries adicionais do SGS) — fora do escopo mínimo
  deste fluxo (ver spec.md, Assumptions).

## Evidência (payload bruto)

```json
[{"data":"01/03/2026","valor":"0.88"},{"data":"01/04/2026","valor":"0.67"},{"data":"01/05/2026","valor":"0.58"}]
```
