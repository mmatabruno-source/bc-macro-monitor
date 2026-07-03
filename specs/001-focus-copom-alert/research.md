# Research: Alerta de Mudança Relevante no Focus para a Próxima Reunião do Copom

## R1 — Formato do payload da API de Expectativas de Mercado (Focus)

- **Status**: ✅ Resolvido em 2026-07-03, via chamadas de teste reais.
- **Decision**: endpoint `ExpectativasMercadoSelic` do serviço Expectativas
  (Olinda), campos `Indicador`, `Data`, `Reuniao`, `Mediana`,
  `numeroRespondentes`, `baseCalculo` (schema completo e regras de seleção
  em `contracts/focus-api.md`).
- **Rationale**: confirmado por 4 chamadas reais (service document,
  `$metadata`, filtro por `Reuniao`, filtro por `Data`), nunca assumido a
  partir de documentação de terceiros.
- **Alternatives considered**: N/A.

## R2 — Como identificar "a próxima reunião do Copom" a partir da resposta

- **Status**: ✅ Resolvido em 2026-07-03, via chamada de teste real.
- **Decision**: entre todas as linhas retornadas para a divulgação mais
  recente (`Data` mais recente), parsear `Reuniao` como `(ano, número)` a
  partir do formato `"R<número>/<ano>"` e escolher a de menor par
  `(ano, número)`. Ver Regra 2 em `contracts/focus-api.md`.
- **Rationale**: evidência empírica mostrou que a API já exclui reuniões
  passadas de cada divulgação — a menor `Reuniao` presente é, por
  construção, a próxima. Isso dispensa qualquer fonte externa de
  calendário (Atas do copom-monitor-pm, release de imprensa, ou tabela
  hardcoded), consistente com FR-002 e com o Princípio VI (API oficial como
  única fonte de verdade, nunca calendário).
- **Alternatives considered**:
  - Manter uma lista de datas de reunião versionada no repositório —
    rejeitada, viola Princípio VI.
  - Derivar o mapeamento `Reuniao` ↔ data real a partir do endpoint de
    Atas do BCB (`sitebcb/copom/atas`, já validado pelo copom-monitor-pm),
    contando reuniões por ano — considerada, mas descartada por ser
    desnecessária: a Regra 2 acima resolve o problema original (identificar
    a próxima reunião) sem precisar de datas de calendário reais, com uma
    fonte de dado a menos para manter e sem a exceção de "hardcode
    revisado anualmente" que o endpoint de Atas exigiria para o horizonte
    sem Ata publicada.

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

Nenhum bloqueio restante. R1 e R2 foram resolvidos com payloads reais em
2026-07-03; `contracts/focus-api.md` está completo e as tarefas de
implementação do cliente HTTP (T004/T012/T015 em `tasks.md`) podem
prosseguir.
