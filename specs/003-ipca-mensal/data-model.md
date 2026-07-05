# Data Model: Notificação da Divulgação Mensal do IPCA

> Mapeamento confirmado contra o contrato real em `contracts/ipca-sgs.md`
> (verificado em 2026-07-03).

## Entidade: DivulgacaoIpca

Representa o valor do IPCA de um mês específico.

| Campo | Tipo | Campo real da API (`bcdata.sgs.433`) | Descrição | Regras |
|---|---|---|---|---|
| `mes_referencia` | string (YYYY-MM) | `data` (`"DD/MM/YYYY"`, `DD="01"`) | Mês a que o valor se refere | Usado como chave de idempotência (FR-002/FR-005); extraído como `data[6:10]-data[3:5]` |
| `variacao_mensal` | number | `valor` (string decimal) | Variação percentual do IPCA no mês | Fonte de verdade para a notificação (FR-003); convertido com `float(valor)` |

## Entidade: RegistroEstadoIpca (chave `ultimo_ipca` em `estado.json`)

| Campo | Tipo | Descrição |
|---|---|---|
| `mes_referencia` | string (YYYY-MM) | Último mês processado com sucesso |
| `variacao_mensal` | number | Valor registrado do último mês processado |

**Transições de estado**:
1. **Vazio → Primeiro mês registrado**: primeira execução do fluxo;
   notificação enviada normalmente (evento discreto, sem necessidade de
   comparação direcional prévia).
2. **Mês registrado → Novo mês**: `mes_referencia` da API é mais recente
   que a registrada → notificação enviada, estado atualizado após
   confirmação.
3. **Mês registrado → Sem mudança**: mesmo `mes_referencia` → nenhuma ação
   (idempotência, FR-005).

## Entidade: LeituraImpactoIpca *(substituída, ver Atualização abaixo)*

> **Atualização (2026-07-05, trilha leve — ver research.md, entrada
> equivalente a R5/R6 do fluxo 002)**: a leitura qualitativa descrita
> abaixo (acelerou/desacelerou, acima/abaixo da meta) foi substituída por
> valores numéricos explícitos, por decisão do usuário. `src/ipca/leitura_impacto.py`
> hoje só expõe `META_INFLACAO_CENTRO` (constante) e
> `calcular_variacao_anualizada` (juros compostos:
> `((1 + variacao_mensal/100)^12 - 1) * 100`) — nenhum enum de direção é
> gerado ou enviado.

## Entidade: GrupoIpca

Representa a variação/peso de um grupo (nível grupo, 9 grupos oficiais)
ou de um item (nível item, dentro de um grupo) do IPCA — mesmo formato
reaproveitado para os dois níveis.

| Campo | Tipo | Descrição |
|---|---|---|
| `nome` | string | Nome do grupo ou item |
| `variacao_mensal` | number | Variação percentual do grupo/item no mês |
| `peso_mensal` | number | Peso do grupo/item na composição do IPCA do mês |

- **Contribuição** (não é campo do modelo, calculada): `variacao_mensal × peso_mensal` — usada para ranquear a tabela de composição por grupo e para selecionar os 3 grupos que mais pressionaram o IPCA para cima (só grupos com `variacao_mensal > 0` entram no ranking de seleção).
- Fonte: IBGE (tabela SIDRA 7060, `servicodados.ibge.gov.br`) — fonte
  secundária e historicamente instável, ver
  `decisoes/composicao-ipca-por-grupo.md`. Falha nessa busca nunca bloqueia
  a notificação principal (FR-003a).

## Entidade: NotificacaoIpca

Mensagem única enviada ao bot dedicado ao fluxo IPCA.

| Campo | Tipo | Descrição |
|---|---|---|
| `mes_referencia` | string | Mês a que a notificação se refere |
| `variacao_mensal` | number | Variação mensal do mês atual |
| `mes_anterior` | number | Variação mensal do mês anterior |
| `mes_ano_anterior` | number \| None | Variação do mesmo mês no ano anterior, se disponível (série de 13 meses) |
| `variacao_anualizada` | number | Projeção anualizada por juros compostos |
| `meta_inflacao` | number | Meta de inflação vigente (constante) |
| `composicao_por_grupo` | list[GrupoIpca] \| None | Tabela dos 9 grupos oficiais, ranqueada por contribuição; `None` se a busca falhar ou o mês divergir (fallback) |
| `detalhamento_top3` | list[(GrupoIpca, list[GrupoIpca])] \| None | Os 3 grupos com maior contribuição positiva, cada um com a lista de seus itens; `None` se não houver grupo positivo ou se a busca de itens falhar/divergir |
