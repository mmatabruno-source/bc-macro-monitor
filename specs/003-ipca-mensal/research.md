# Research: Notificação da Divulgação Mensal do IPCA

## R1 — Formato do payload da série 433 do SGS

- **Status**: 🔴 **BLOQUEADO — aguardando payload real.**
- **Decision**: Nenhuma. Por Princípio II, este projeto não escreve
  cliente HTTP nem parser a partir de documentação pública/terceiros. O
  endpoint candidato levantado por pesquisa pública é:
  ```
  https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados/ultimos/3?formato=json
  ```
  (últimos 3 valores, para já ver ao menos uma transição de mês na
  resposta).
- **Ação necessária**: pedir ao usuário para colar a resposta real dessa
  URL (navegador, curl ou Postman).

## R2 — Núcleos de inflação (se disponíveis)

- **Status**: 🟡 Depende do payload real de R1.
- **Decision**: por ora, fora do escopo mínimo (FR-003 só exige o número
  objetivo da série 433, ver Assumption na spec). Se o usuário quiser
  incluir núcleos, isso vai exigir identificar as séries SGS adicionais
  correspondentes (números de série distintos) e um novo ciclo de
  verificação de contrato — tratado como melhoria futura, não nesta
  primeira versão do fluxo.

## R3 — Centro da meta de inflação vigente

- **Status**: ✅ Resolvido (nível de decisão de produto, não de API).
- **Decision**: valor mantido como constante no código (ex.:
  `META_INFLACAO_CENTRO = 3.0`), revisado manualmente uma vez por ano
  quando o CMN divulgar a meta do próximo ano — documentado como Assumption
  na spec, não viola Princípio VI (não decide se o fluxo verifica a série,
  só informa o texto da leitura de impacto).
- **Rationale**: a meta de inflação é definida por resolução do CMN,
  publicada por comunicado oficial, não por uma API de atualização
  contínua — não há uma "fonte de verdade viva" a consultar por chamada
  HTTP para este dado específico.
- **Alternatives considered**: nenhuma API foi encontrada (nem buscada,
  por não ser necessário) para este parâmetro; tratá-lo como constante é
  consistente com o padrão de exceção documentado no Princípio VI para
  parâmetros de política raramente alterados.

## R4 — Regra de leitura de impacto (sem LLM)

- **Status**: ✅ Resolvido, via `/speckit-clarify` na spec.
- **Decision**: comparar o valor do mês com o valor do mês anterior
  (acelerou/desacelerou) e com o centro da meta de inflação (R3)
  (acima/abaixo/em linha), montando uma frase curta e determinística.
- **Rationale**: decisão explícita do usuário, evita custo e dependência
  de uma chave de API de LLM para este fluxo específico.
- **Alternatives considered**: LLM (como Ata/Relatório) — rejeitada por
  decisão do usuário, não há "tom" de texto a interpretar aqui.

## Resumo de bloqueios para a Phase 1

Apenas R1 bloqueia a conclusão de `contracts/ipca-sgs.md` com o schema de
campos. `data-model.md` e `quickstart.md` serão escritos em termos de
conceitos de negócio (mês de referência, valor mensal) sem depender do
nome exato dos campos JSON.
