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

## Resumo de bloqueios para a Phase 1

Nenhum bloqueio restante. R1–R4 resolvidos com payload real e decisão do
usuário em 2026-07-03; `contracts/relatorio-dataset.md` está completo.
