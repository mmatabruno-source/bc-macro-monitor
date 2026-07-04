# Research: Notificação da Divulgação Mensal do IPCA

## R1 — Formato do payload da série 433 do SGS

- **Status**: ✅ Resolvido em 2026-07-03, via chamada de teste real.
- **Decision**: endpoint `bcdata.sgs.433/dados/ultimos/N`, campos `data`
  (`"DD/MM/YYYY"`, sempre com `DD="01"`, representando o mês de
  referência) e `valor` (string decimal, variação percentual mensal).
  Schema completo em `contracts/ipca-sgs.md`.
- **Rationale**: confirmado por chamada real
  (`ultimos/3` → `[{"data":"01/03/2026","valor":"0.88"}, ...]`), nunca
  assumido a partir de documentação de terceiros.
- **Alternatives considered**: N/A.

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

## R5 — Composição do IPCA por grupo (variação + peso), fonte de dados

- **Status**: ✅ Resolvido — decisão de arquitetura tomada em 2026-07-04
  após investigação extensiva com testes reais no GitHub Actions (não
  hipotéticos). Ver detalhes completos em
  `specs/003-ipca-mensal/decisoes/composicao-ipca-por-grupo.md`.
- **Decision**: implementar com `servicodados.ibge.gov.br` (API v3 de
  Agregados) como fonte, **envolto em fallback obrigatório** — se a
  chamada falhar, o fluxo envia a mensagem do IPCA sem a tabela de
  composição (só variação geral + leitura), nunca bloqueando o alerta
  principal.
- **Rationale (resumo)**: não existe API do BC com essa abertura, só o
  IBGE tem. Testado em produção real (GitHub Actions): três fontes
  candidatas (`apisidra.ibge.gov.br`, `servicodados.ibge.gov.br`,
  `www.ipeadata.gov.br`) mostraram o mesmo padrão de instabilidade
  errática (ora respondem em ~1s, ora dão `ConnectTimeout` completo,
  sem relação com sintaxe de URL, IPv4/IPv6, ou horário) — não é um bug
  de código, é rede real entre os runners do GitHub Actions e infra
  `.gov.br`. Self-hosted (runner com IP residencial) resolveria de
  verdade, mas foi adiado até haver dados de taxa de falha em produção.
- **Alternatives considered**: `apisidra.ibge.gov.br` (SIDRA antiga,
  formato "values") — mesma instabilidade, descartada por não ser a
  API recomendada pela comunidade (wrappers como `sidrapy` já usam a
  v3). `www.ipeadata.gov.br` (OData4) — não tem confirmação de que
  possui peso mensal por grupo (só variação), sintaxe de `$filter`
  nunca validada com sucesso (sempre 400 ou timeout), e mesma
  instabilidade de rede — descartada por ora.

## R6 — Detalhamento por item dos 3 grupos que mais pressionaram o IPCA para cima

- **Status**: ✅ Resolvido — implementado como extensão do R5, sem
  interação com o bot (sem polling/webhook, que exigiriam infra sempre
  ligada fora do modelo de cron). Ver detalhes em
  `specs/003-ipca-mensal/decisoes/composicao-ipca-por-grupo.md`.
- **Decision**: usar `classificacao=315[all]` na mesma tabela 7060 do
  IBGE (segunda chamada HTTP independente, `buscar_itens_por_grupo`),
  filtrando pelo prefixo numérico do `D4N` (4 dígitos = nível item);
  selecionar os 3 grupos com maior `variação_mensal × peso_mensal` entre
  os de variação positiva, e mostrar todos os itens de cada um. Mesmo
  fallback obrigatório de R5 (falha ou mês divergente omite só essa
  seção da mensagem).
- **Rationale**: decisão do usuário — evita construir infraestrutura de
  interação (bot respondendo a comandos) mantendo o modelo de push
  periódico já existente.
- **Alternatives considered**: interação via bot (comandos, ex.
  `/detalhe Alimentação`) — rejeitada por exigir self-hosted/polling
  contínuo, fora do escopo do cron atual.

## Resumo de bloqueios para a Phase 1

Nenhum bloqueio restante. R1 resolvido com payload real em 2026-07-03;
`contracts/ipca-sgs.md` está completo e as tarefas de implementação do
cliente HTTP podem prosseguir. R5 documentado em decisão separada.
