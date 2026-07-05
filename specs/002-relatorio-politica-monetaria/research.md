# Research: Notificação da Publicação do Relatório de Política Monetária

## R1 — Formato do payload do dataset de Relatórios de Política Monetária

- **Status**: ✅ Resolvido em 2026-07-03, via chamada de teste real.
- **Decision**: endpoint
  `https://www.bcb.gov.br/api/servico/sitebcb/ri/relatorios?quantidade=N`,
  campos `identificador`, `dataReferencia`, `url` (PDF), `linkPaginaBC`,
  `edicao`, `volume`. Schema completo em `contracts/relatorio-dataset.md`.
- **Rationale**: confirmado por chamada real
  (`quantidade=5` → lista de 5 relatórios, do mais recente ao mais antigo),
  nunca assumido a partir de documentação de terceiros. O usuário também
  colou o texto da página do dataset, que confirma oficialmente (fonte
  primária do BCB) que o relatório "é distribuído como um documento PDF".
- **Alternatives considered**: N/A.

## R2 — Conteúdo do relatório: PDF ou estruturado?

- **Status**: ✅ Resolvido em 2026-07-03 — **é só PDF**, confirmado tanto
  pelo payload real (nenhum campo de texto estruturado, só metadados e
  `url` do PDF) quanto pela descrição oficial da página do dataset.
- **Decision**: o conteúdo da análise crítica (User Story 2) precisa
  processar o PDF diretamente — não há atalho estruturado.

## R3 — Mecanismo de geração da análise crítica (LLM ou não)

- **Status**: ✅ Resolvido em 2026-07-03, via decisão do usuário.
- **Decision**: baixar os bytes do PDF (a partir do campo `url`) e enviá-los
  diretamente como bloco de documento em uma chamada à API da Anthropic
  (Claude), que tem suporte nativo à leitura de PDF — **sem nenhuma
  biblioteca de extração de texto de PDF** (`pypdf` ou similar).
- **Rationale**: elimina uma dependência inteira (parser de PDF) mantendo
  a mesma simplicidade de dependências do projeto (Princípio VII);
  reaproveita o padrão de análise via LLM já validado no copom-monitor-pm
  para Atas, adaptado para receber um documento em vez de texto puro.
  Novo segredo necessário: `ANTHROPIC_API_KEY` (GitHub Secret — não é um
  "bot" do Telegram, então não conflita com o Princípio IV).
- **Alternatives considered**:
  - Extrair texto do PDF localmente com `pypdf` e enviar texto puro ao
    LLM — rejeitada por introduzir uma dependência a mais sem necessidade,
    já que a Claude API lê PDF nativamente.
  - Não tentar análise automática, só aviso + link — rejeitada pelo
    usuário; a análise crítica é o valor central da User Story 2.

## R4 — Chave de idempotência

- **Status**: ✅ Resolvido — `identificador` (`"YYYYMM"`), mais simples e
  estável que derivar de `dataReferencia`.

## R5 — Endpoint renomeado (`ri` → `rpm`), descoberto em produção

- **Status**: ✅ Resolvido em 2026-07-05, via chamada de teste real
  (trilha leve — registro conforme constituição v2.0.0, Princípio I).
- **Contexto**: o fluxo continuava "avisando" sobre o mesmo relatório
  (`202412`, dez/2024) meses depois em produção. Não era bug de
  idempotência — era a fonte de dados desatualizada.
- **Decision**: o documento foi renomeado de "Relatório de Inflação" para
  "Relatório de Política Monetária" a partir da edição de mar/2025
  (`202503`). O endpoint de R1 (`sitebcb/ri/relatorios`) é especificamente
  o dataset do nome antigo e parou de receber itens novos, travado em
  `202412`. O endpoint correto e atual é `sitebcb/rpm/relatorios` — mesmo
  schema, confirmado com payload real (`identificador` mais recente:
  `202606`, referência 2026-06-25). `contracts/relatorio-dataset.md`
  atualizado com o payload novo.
- **Rationale**: mesmo padrão de risco do Princípio II — um contrato
  verificado pode ficar obsoleto se a fonte mudar de comportamento sem
  aviso; a verificação precisa ser refeita quando o comportamento em
  produção diverge do esperado, não assumida como permanente.

## R6 — Reformulação da análise crítica: visão cidadão + investidor

- **Status**: ✅ Resolvido em 2026-07-05, por decisão do usuário (trilha
  leve — registro conforme constituição v2.0.0, Princípio I).
- **Decision**: as 3 seções originais (cenário macro, projeções de
  inflação, implicação para portfólio) foram substituídas por 2: visão
  crítica para o cidadão (o que é relevante estar consciente sobre o
  país, a partir do relatório) e visão do investidor pessoa física
  residente no Brasil (o que o relatório estimula ou desestimula fazer).
  Cada seção em tópicos curtos com "▪️", não em parágrafos corridos.
  Sequência de notificação passa de 4 para 3 mensagens (aviso + 2
  análises). `AnaliseCritica` e os marcadores do parser (`gerador_analise.py`)
  atualizados de acordo (`data-model.md` já reflete isso).
- **Rationale**: decisão de produto do usuário — o formato anterior
  (leitura mais técnica de portfólio) não era o que ele queria acompanhar;
  o novo formato serve tanto a leitura cidadã quanto a de investidor
  pessoa física, ambas em formato direto e escaneável.

## Resumo de bloqueios para a Phase 1

Nenhum bloqueio restante. R1–R6 resolvidos com payload real e decisões do
usuário; `contracts/relatorio-dataset.md` e `data-model.md` estão
atualizados com o estado atual (R5, R6).
