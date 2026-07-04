# Data Model: Resumo Semanal do Focus

> Mapeamento confirmado contra `contracts/expectativas-anuais.md`.

## Entidade: ValorIndicadorAno

| Campo | Tipo | Campo real da API | Descrição |
|---|---|---|---|
| `indicador` | string | `Indicador` | `"IPCA"`, `"Selic"`, `"Câmbio"` ou `"PIB Total"` |
| `ano` | string (`"YYYY"`) | `DataReferencia` | Ano a que o valor se refere |
| `valor` | number | `Mediana` (linha com `baseCalculo=0`) | Fonte de verdade |

## Entidade: DivulgacaoFocusResumo

| Campo | Tipo | Descrição |
|---|---|---|
| `data_referencia` | string (`"YYYY-MM-DD"`) | Campo `Data` da divulgação — chave de idempotência (FR-002/FR-008) |
| `valores` | list[ValorIndicadorAno] | 4 indicadores × 5 anos (até 20 itens; menos se algum ano não vier na resposta) |

## Entidade: RegistroEstadoFocusResumo (chave `ultimo_resumo_focus` em `estado.json`)

| Campo | Tipo | Descrição |
|---|---|---|
| `data_referencia` | string | Última divulgação processada com sucesso |
| `valores` | dict | Mapa `"{indicador}:{ano}"` → `valor`, usado para calcular direção na próxima checagem (FR-004) |

**Transições de estado**:
1. **Vazio → Primeira divulgação registrada**: todos os valores aparecem
   sem indicação de direção (FR-005).
2. **Registro existente → Nova divulgação**: `Data` mais recente que a
   registrada → mensagem com direção por (indicador, ano) presente no
   registro anterior; itens novos (ex.: ano que entrou na janela de 5
   anos) aparecem sem direção.
3. **Registro existente → Sem mudança**: mesma `Data` → nenhuma ação
   (FR-008).

## Entidade: MensagemResumoFocus

Mensagem única enviada ao bot do fluxo Focus.

| Campo | Tipo | Descrição |
|---|---|---|
| `data_referencia` | string | Data da divulgação |
| `linhas` | list | Para cada indicador: nome + lista de (ano, valor, direção\|None) |

`direção` ∈ {`subiu`, `desceu`, `manteve`, `None` (sem histórico anterior)}.
