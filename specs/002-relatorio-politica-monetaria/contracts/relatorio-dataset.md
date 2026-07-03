# Contrato: Dataset de Relatórios de Política Monetária — BLOQUEADO

**Status**: 🔴 **NÃO VERIFICADO. Não usar para implementação.**

Por Princípio II da constituição, este arquivo não pode conter um schema
de campos até que o payload real de uma chamada de teste seja fornecido
pelo usuário. Além disso, este contrato também depende da decisão
PDF-vs-estruturado (ver `research.md`, R2), que só pode ser tomada depois
de ver o payload real.

## O que falta

1. Abrir `https://dadosabertos.bcb.gov.br/dataset/relatorios-de-inflacao-publicados`
   no navegador e colar aqui a URL real de acesso aos dados (o Portal de
   Dados Abertos costuma expor um recurso/API específico por dataset —
   pode ser um endpoint JSON, um CSV, ou outro formato).
2. Colar a resposta real dessa chamada.

## O que este contrato precisa documentar assim que o payload chegar

- Nome exato dos campos que contêm: período/trimestre de referência, data
  de publicação, link para o documento oficial.
- Se o conteúdo do relatório está disponível de forma estruturada (texto,
  seções, tabelas de projeção) ou apenas como link de PDF.
- Se estruturado: nomes dos campos de cenário macro e projeções de
  inflação.
- Se só PDF: isso vira uma pergunta de `/speckit-clarify` antes de
  prosseguir (ver `research.md`, R2) — não assumir biblioteca de parsing.

## Tarefas bloqueadas por este contrato

Todas as tarefas de implementação de `src/relatorio/cliente_dataset.py`,
`src/relatorio/extrator_conteudo.py`, `src/relatorio/gerador_analise.py` e
`tests/contract/test_contrato_relatorio.py` em `tasks.md` ficam bloqueadas
até este arquivo ser preenchido a partir de um payload real e a decisão
PDF/LLM ser tomada.
