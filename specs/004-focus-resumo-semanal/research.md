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

- **Status**: ✅ Resolvido, decisão direta do usuário: comparar contra o
  último valor registrado no histórico próprio deste fluxo (por
  indicador/ano), não contra o "há 1 semana" que o boletim oficial expõe
  (que não está disponível via API de qualquer forma). Sem contador de
  quantas semanas o comportamento se repete.

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
