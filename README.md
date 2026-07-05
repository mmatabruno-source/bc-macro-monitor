# bc-macro-monitor

Monitor automático de indicadores macroeconômicos brasileiros, com alertas
via Telegram para apoio a decisões de portfólio. Roda inteiramente via
GitHub Actions (cron), sem servidor dedicado — o estado e o histórico ficam
versionados no próprio repositório.

## Fluxos

- **Focus/Copom** — expectativa de mediana da Selic para a próxima reunião
  do Copom, comparada à Selic vigente.
- **Resumo Semanal do Focus** — IPCA, Selic, Câmbio e PIB projetados pelo
  Focus, comparados à divulgação da semana anterior (mesmo bot do
  Focus/Copom, por decisão de produto — ver `specs/004-focus-resumo-semanal`).
- **IPCA** — variação mensal, composição por grupo e detalhamento por item
  dos grupos que mais pressionaram para cima.
- **Relatório de Política Monetária** — aviso de publicação e análise
  crítica (visão do cidadão + visão do investidor) via Claude API lendo o
  PDF nativamente.

## Desenvolvimento

Este projeto segue Spec-Driven Development (GitHub Spec Kit) para features
novas e mudanças de contrato/modelo de dados — ver
`.specify/memory/constitution.md` para os princípios e `specs/` para cada
feature. Ajustes cosméticos e de configuração podem ser feitos por edição
direta, registrados no `research.md` da feature afetada.

Todo PR roda a suíte de testes automaticamente (`.github/workflows/ci.yml`)
antes de poder ser mergeado.
