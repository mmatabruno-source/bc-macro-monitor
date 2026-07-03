# Data Model: Notificação da Divulgação Mensal do IPCA

> Nomes de campo conceituais (nível de negócio). Nomes reais de campos JSON
> só serão definidos em `contracts/ipca-sgs.md` depois que o payload real
> for verificado (Princípio II) — ver `research.md`, item R1.

## Entidade: DivulgacaoIpca

Representa o valor do IPCA de um mês específico.

| Campo | Tipo | Descrição | Regras |
|---|---|---|---|
| `mes_referencia` | string (YYYY-MM) | Mês a que o valor se refere | Usado como chave de idempotência (FR-002/FR-005) |
| `variacao_mensal` | number | Variação percentual do IPCA no mês | Fonte de verdade para a notificação (FR-003) |

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

## Entidade: LeituraImpactoIpca

Texto curto anexado à notificação, gerado por regra determinística
(FR-009, R4 em research.md):

| Campo | Tipo | Descrição |
|---|---|---|
| `direcao_vs_mes_anterior` | enum: `acelerou` \| `desacelerou` \| `estavel` | Comparação com `variacao_mensal` do mês anterior processado |
| `posicao_vs_meta` | enum: `acima` \| `abaixo` \| `em_linha` | Comparação com o centro da meta de inflação vigente (constante, ver research.md R3) |

## Entidade: NotificacaoIpca

Mensagem única enviada ao bot dedicado ao fluxo IPCA.

| Campo | Tipo | Descrição |
|---|---|---|
| `mes_referencia` | string | Mês a que a notificação se refere |
| `variacao_mensal` | number | Número objetivo do mês |
| `leitura_impacto` | `LeituraImpactoIpca` | Frase curta gerada pela regra determinística |
