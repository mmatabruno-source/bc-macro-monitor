# Quickstart: Validação do Resumo Semanal do Focus

## Pré-requisitos

- Python 3.12 instalado.
- `FOCUS_TELEGRAM_BOT_TOKEN`/`FOCUS_TELEGRAM_CHAT_ID` disponíveis (mesmo
  bot do fluxo Focus/Copom).

## Cenários de validação

1. **Primeira divulgação (sem histórico)**
   - Rodar `src/focus_resumo/fluxo.py` com `estado.json` sem
     `ultimo_resumo_focus`, usando a fixture real
     (`tests/fixtures/expectativas_anuais_2026-06-26.json`).
   - Esperado: mensagem com os 4 indicadores × 5 anos, todos sem
     indicação de direção; `estado.json` atualizado após confirmação.

2. **Nova divulgação (com histórico)**
   - Rodar com `estado.json` já contendo um registro anterior e uma
     fixture com `Data` mais recente e valores diferentes para
     IPCA/2026.
   - Esperado: mensagem com direção correta (subiu/desceu/manteve) para
     os itens com histórico; sem contador de sequência em nenhum lugar.

3. **Mesma divulgação relida (idempotência)**
   - Rodar novamente com a mesma fixture do cenário 2.
   - Esperado: nenhuma mensagem; `estado.json` inalterado.

4. **Falha isolada**
   - Forçar exceção na checagem (ex.: mockar timeout).
   - Esperado: aviso de falha; `estado.json` inalterado; outros fluxos
     não afetados.

## Cenário com API real

5. **Chamada real à API**
   - Rodar `src/focus_resumo/cliente_expectativas_anuais.py` contra a API
     real e confirmar que os 4 indicadores × 5 anos são extraídos
     corretamente para a divulgação mais recente.
