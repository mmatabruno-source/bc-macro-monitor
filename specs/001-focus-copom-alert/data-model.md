# Data Model: Alerta de Mudança Relevante no Focus para a Próxima Reunião do Copom

> Mapeamento confirmado contra o contrato real em `contracts/focus-api.md`
> (verificado em 2026-07-03).

## Entidade: DivulgacaoFocus

Representa uma publicação específica do boletim Focus para a próxima
reunião do Copom, no momento em que foi lida pelo sistema.

| Campo | Tipo | Campo real da API (`ExpectativasMercadoSelic`) | Descrição | Regras |
|---|---|---|---|---|
| `reuniao_id` | string | `Reuniao` (ex.: `"R5/2026"`) | Identificador da reunião do Copom a que a divulgação se refere | Escolhida como a de menor `(ano, número)` entre as `Reuniao` presentes na divulgação mais recente (contracts/focus-api.md, Regra 2); nunca hardcoded |
| `data_referencia` | date (ISO 8601) | `Data` | Data de referência da divulgação/pesquisa Focus | Usada como chave de idempotência (FR-004a) — distingue "nova divulgação" de "mesma divulgação relida" |
| `mediana_selic` | number | `Mediana` (linha com `baseCalculo = 0`) | Mediana das expectativas de mercado para a Selic nessa reunião | Única estatística usada como fonte de verdade (FR-011); `Media`, `DesvioPadrao`, `Minimo`, `Maximo` são ignorados; `baseCalculo = 1` é ignorado (contracts/focus-api.md, Regra 1) |

**Regras de validação**:
- `data_referencia` MUST ser estritamente mais recente que a última
  divulgação processada da mesma `reuniao_id` para ser considerada nova
  (FR-004a).
- `reuniao_id` MUST ser calculada tomando o menor `(ano, número)` entre
  todas as linhas com `Data` igual à divulgação mais recente e
  `baseCalculo = 0` (contracts/focus-api.md, Regra 2). Reuniões passadas
  nunca aparecem na resposta da API, então esta regra basta.
- Quando `reuniao_id` muda em relação ao estado anterior (a reunião
  monitorada virou passado), a nova `DivulgacaoFocus` é tratada como
  primeira leitura daquela reunião — sem comparação direcional (FR-008).

## Entidade: RegistroEstadoFocus (chave `ultima_expectativa_copom` em `estado.json`)

Representa a última `DivulgacaoFocus` processada com sucesso (isto é,
notificada e confirmada) para o fluxo Focus.

| Campo | Tipo | Descrição |
|---|---|---|
| `reuniao_id` | string | Reunião a que a última divulgação processada se refere |
| `data_referencia` | date (ISO 8601) | Data de referência da última divulgação processada |
| `mediana_selic` | number | Mediana registrada na última divulgação processada |

**Transições de estado**:
1. **Vazio → Primeira divulgação registrada**: ocorre na primeiríssima
   execução do fluxo, ou logo após a troca de reunião monitorada (FR-008).
   Notificação enviada é informativa, sem direção.
2. **Divulgação registrada → Nova divulgação (mesma reunião)**: ocorre
   quando `data_referencia` da API é mais recente que a registrada. Gera
   notificação com comparação subiu/desceu/manteve (FR-005).
3. **Divulgação registrada → Sem mudança de estado**: ocorre quando
   `data_referencia` da API é igual à registrada (mesma divulgação relida).
   Nenhuma notificação, nenhuma escrita em `estado.json` (FR-007).

O registro em `estado.json` só é atualizado **após** confirmação de envio
bem-sucedido da notificação correspondente (FR-006, Princípio V).

## Entidade: RegistroHistoricoFocus (`historico/focus/<data_referencia>.json` ou `.md`)

Cópia arquivada de cada `DivulgacaoFocus` processada com sucesso, para
auditoria e para permitir reconstruir a série de divulgações já notificadas.
Contém os mesmos campos de `DivulgacaoFocus`, mais o texto da notificação
enviada e o timestamp de envio.

## Entidade: NotificacaoFocus

Mensagem enviada ao bot Telegram dedicado ao fluxo Focus.

| Campo | Tipo | Descrição |
|---|---|---|
| `reuniao_id` | string | Reunião a que a notificação se refere |
| `mediana_anterior` | number \| null | Valor da divulgação anterior da mesma reunião; `null` na primeira divulgação de uma reunião |
| `mediana_nova` | number | Valor da divulgação atual |
| `direcao` | enum: `subiu` \| `desceu` \| `manteve` \| `inicial` | `inicial` quando `mediana_anterior` é `null` (sem comparação possível) |
