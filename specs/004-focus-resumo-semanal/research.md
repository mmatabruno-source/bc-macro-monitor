# Research: Resumo Semanal do Focus

## R1 — Formato do payload de ExpectativasMercadoAnuais

- **Status**: ✅ Resolvido em 2026-07-04, via chamadas de teste reais
  (ver `contracts/expectativas-anuais.md`).

## R2 — Como identificar a divulgação mais recente

- **Status**: ✅ Resolvido — mesma estratégia do fluxo 001: `$orderby=Data
  desc&$top=1` para descobrir a `Data` mais recente, depois filtrar por
  essa `Data` para pegar os 4 indicadores × 5 anos.

## R3 — Anos a exibir

- **Status**: ✅ Resolvido, decisão direta do usuário: ano corrente da
  execução + 3 anos seguintes (4 no total — reduzido de 5 em 2026-07-05,
  trilha leve, por pedido do usuário), calculado dinamicamente
  (`datetime.now().year` até `+3`), nunca uma lista fixa.

## R4 — Comparação semanal

- **Status**: ✅ Resolvido, decisão direta do usuário: comparar contra a
  divulgação anterior (por indicador/ano), não contra o "há 1 semana" que
  o boletim oficial expõe (que não está disponível via API de qualquer
  forma). Sem contador de quantas semanas o comportamento se repete.
- **Atualização (2026-07-05, trilha leve)**: a implementação original
  comparava contra o valor persistido em `estado.json` da execução
  anterior deste próprio fluxo. O usuário pediu explicitamente que a
  comparação **sempre** busque a divulgação mais recente E a penúltima
  diretamente da API (2 chamadas), nunca dependendo de estado local —
  motivado por um teste manual em que o estado local tinha sido
  sobrescrito com valores idênticos aos atuais (artefato do próprio
  teste), mascarando se a comparação de verdade funcionava. Agora
  `buscar_datas_recentes()` busca as 2 datas mais recentes distintas
  (`$top=100` — cada data tem várias linhas, uma por indicador/ano) e
  `buscar_divulgacao(data)` busca os valores de uma data específica;
  `estado.json` continua guardando `data_referencia` (idempotência) e
  `valores` (auditoria), mas não é mais usado para calcular a direção.
  Falha ao buscar a penúltima é tratada com o mesmo padrão de fallback
  dos demais fluxos (mensagem principal sai sem a comparação).

## R5 — Encoding de URL

- **Status**: ✅ Resolvido, reaproveitando a correção já validada em
  produção no fluxo 001 (T030): usar `urlencode(..., quote_via=quote)` em
  vez de `params=` do `requests`, para evitar `+` em vez de `%20` e o
  consequente 400 Bad Request.

## R6 — Reformatação da direção: texto → seta + p.p. (trilha leve)

- **Status**: ✅ Resolvido em 2026-07-05, decisão direta do usuário.
- **Decision**: a indicação de direção deixou de ser texto
  "(subiu)/(desceu)/(manteve)" e virou seta com a magnitude da variação
  entre parênteses: `(▲ X,XX p.p.)` / `(▼ X,XX p.p.)` / `(= 0 p.p.)` —
  sempre com a unidade `p.p.` presente, mesmo quando não há mudança.
  Títulos de indicador ganharam a unidade explícita (`IPCA (a.a.)`,
  `Selic (a.a.)`, `Câmbio (BRL/USD)`, `PIB (var. sobre o ano anterior)`),
  e o PIB ganhou sufixo `%` nos valores.
- **Rationale**: decisão de produto do usuário, buscando um formato mais
  direto/visual do que texto entre parênteses sem magnitude.

## Resumo de bloqueios para a Phase 1

Nenhum bloqueio. Todas as decisões técnicas já resolvidas com payload real
e decisões diretas do usuário nesta mesma conversa.
