# Research: Notificação da Publicação do Relatório de Política Monetária

## R1 — Formato do payload do dataset de Relatórios de Política Monetária

- **Status**: 🔴 **BLOQUEADO — aguardando payload real.**
- **Decision**: Nenhuma. Por Princípio II, este projeto não escreve
  cliente HTTP nem parser a partir de documentação pública/terceiros. O
  dataset candidato levantado por pesquisa pública é
  `relatorios-de-inflacao-publicados`, no Portal de Dados Abertos do BCB
  (`dadosabertos.bcb.gov.br`), mas isso é apenas uma hipótese de onde
  consultar.
- **Ação necessária**: pedir ao usuário para:
  1. Abrir o dataset no Portal de Dados Abertos do BCB
     (`https://dadosabertos.bcb.gov.br/dataset/relatorios-de-inflacao-publicados`)
     e colar a URL real de acesso aos dados (a página do dataset costuma
     expor um link de API/recurso, formato CSV/JSON/API).
  2. Fazer a chamada de teste a esse link e colar a resposta real.

## R2 — Conteúdo do relatório: PDF ou estruturado?

- **Status**: 🔴 **BLOQUEADO — depende de R1.**
- **Decision**: Nenhuma ainda. Por instrução explícita do usuário, esta
  decisão só pode ser tomada via `/speckit-clarify` depois que o payload
  de R1 mostrar se o dataset expõe apenas um link de PDF ou também
  conteúdo estruturado (texto, seções, tabelas de projeção).
- **Cenários possíveis a decidir quando o payload chegar**:
  - Se houver conteúdo estruturado (ex.: texto das seções, tabela de
    projeções em formato de dados): parsear diretamente, sem LLM
    necessariamente.
  - Se houver apenas um link de PDF: decidir entre (a) extrair texto bruto
    do PDF com uma biblioteca simples e resumir via LLM, ou (b) não tentar
    extrair automaticamente e enviar apenas o aviso de publicação com link
    (reduzindo a User Story 2 a um nível mais básico), ou (c) outra
    abordagem a discutir.
- **Ação necessária**: nenhuma adicional além de R1 — a decisão é tomada
  no mesmo momento, com o mesmo payload.

## R3 — Mecanismo de geração da análise crítica (LLM ou não)

- **Status**: 🟡 Depende de R2.
- **Decision**: adiada. Se R2 concluir que há conteúdo estruturado
  suficiente, uma regra determinística pode bastar (como decidido para o
  fluxo IPCA). Se depender de interpretar texto corrido (PDF ou seções
  longas), um LLM é o caminho mais plausível, reaproveitando o padrão já
  validado no copom-monitor-pm para análise de Ata — mas isso introduz uma
  nova chave de API (`ANTHROPIC_API_KEY` ou similar) como GitHub Secret,
  compartilhada entre os fluxos que precisarem de LLM (não é um "bot"
  então não conflita com o Princípio IV de bot dedicado por fluxo).
- **Ação necessária**: nenhuma adicional além de R1/R2.

## Resumo de bloqueios para a Phase 1

R1 e R2 (e por consequência R3) bloqueiam a conclusão de
`contracts/relatorio-dataset.md` e de `data-model.md`/`quickstart.md` na
parte que depende do mecanismo de extração/análise. As partes de negócio
puramente estruturais (ex.: chave de estado, fallback de FR-006) podem ser
descritas em termos conceituais desde já.
