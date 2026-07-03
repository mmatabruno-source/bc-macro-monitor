# Research: Alerta de Mudança Relevante no Focus para a Próxima Reunião do Copom

## R1 — Formato do payload da API de Expectativas de Mercado (Focus)

- **Status**: 🔴 **BLOQUEADO — sem decisão possível ainda.**
- **Decision**: Nenhuma. Por Princípio II da constituição (nunca codificar
  contra um contrato de API não verificado), este projeto não escreve
  cliente HTTP, parser ou schema de campos a partir de documentação
  pública/terceiros. O endpoint candidato levantado por pesquisa pública é
  `https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/...`
  (serviço `ExpectativasMercadoSelic`), mas isso é apenas uma hipótese de
  onde consultar — não uma confirmação de formato.
- **Rationale**: no projeto irmão copom-monitor-pm, assumir o formato de um
  payload não verificado causou retrabalho em produção; este projeto não
  repete o erro.
- **Alternatives considered**: N/A — não há alternativa a "esperar o
  payload real", pois é uma regra do projeto, não uma escolha técnica.
- **Ação necessária antes da Phase 1 poder ser concluída para este item**:
  o usuário precisa colar a resposta JSON real de uma chamada de teste
  (navegador, curl ou Postman) ao endpoint candidato, filtrando pela
  reunião de Copom mais próxima. Isso vira `contracts/focus-api.md` assim
  que disponível.

## R2 — Como identificar "a próxima reunião do Copom" a partir da resposta

- **Status**: 🟡 Depende do payload real (R1) para a implementação exata,
  mas a estratégia geral já pode ser decidida no nível de spec/plano.
- **Decision**: a lógica de negócio (independente do formato exato do
  campo) é: dentre as reuniões futuras presentes na resposta, escolher a
  de data mais próxima da data de execução. Isso é testável com dados
  simulados (fixtures) antes mesmo do contrato real, desde que os testes de
  contrato fiquem separados dos testes de lógica pura.
- **Rationale**: consistente com FR-002 do spec (API oficial como fonte de
  verdade para qual é a próxima reunião, nunca calendário fixo).
- **Alternatives considered**: manter uma lista de datas de reunião
  versionada no repositório — rejeitada, pois viola Princípio VI
  (calendário nunca decide, só pode ajustar frequência de checagem).

## R3 — Padrões de resiliência a reaproveitar do copom-monitor-pm

- **Status**: ✅ Resolvido — reaproveitar diretamente, adaptado para
  múltiplos bots.
- **Decision**: reaproveitar as funções `_retentavel`,
  `_espera_para_tentativa`, `_sanitizar`, `_executar_isolado` e a assinatura
  `enviar_mensagem(texto, token, chat_id)` do projeto irmão, migradas para
  `src/comum/` e compartilhadas pelos três fluxos deste repositório.
- **Rationale**: já validado em produção; reescrever do zero violaria
  Princípio VII (simplicidade) e arriscaria reintroduzir bugs já
  corrigidos.
- **Alternatives considered**: reimplementar retry/fallback específico para
  este fluxo — rejeitado, pois não há necessidade diferente que justifique
  duplicar a lógica.

## R4 — Onde e como persistir o estado deste fluxo

- **Status**: ✅ Resolvido.
- **Decision**: chave `ultima_expectativa_copom` em `estado.json`, com o
  formato `{"reuniao": "<identificador/data da reunião>", "data_referencia_divulgacao": "<data da divulgação Focus>", "mediana": <número>}`.
  Histórico de cada divulgação processada gravado como um arquivo em
  `historico/focus/` (nome baseado na data de referência da divulgação).
- **Rationale**: consistente com FR-004a/FR-006/FR-007 (idempotência por
  divulgação, não apenas por valor) e com a convenção de armazenamento do
  Princípio III da constituição.
- **Alternatives considered**: guardar apenas o valor da mediana sem a data
  de referência — rejeitado, pois não permitiria distinguir "mesma
  divulgação relida" de "nova divulgação com o mesmo valor", violando
  FR-004a.

## Resumo de bloqueios para a Phase 1

Apenas o item R1 (formato exato do payload) bloqueia a conclusão de
`contracts/focus-api.md` com o schema de campos. Os demais artefatos de
Phase 1 (`data-model.md`, `quickstart.md`) podem ser escritos em termos de
conceitos de negócio (mediana, divulgação, reunião) sem depender do nome
exato dos campos JSON, e serão refinados quando o contrato real chegar.
