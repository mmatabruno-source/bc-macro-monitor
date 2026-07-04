# Quickstart: Validação do Fluxo IPCA

## Pré-requisitos

- Python 3.12 instalado.
- Payload real da série 433 fornecido e `contracts/ipca-sgs.md` preenchido
  (bloqueio do Princípio II resolvido) — sem isso, só os cenários 1–4
  abaixo (fixtures simuladas) podem ser executados.
- Bot do Telegram dedicado ao fluxo IPCA criado, com `IPCA_TELEGRAM_BOT_TOKEN`
  e `IPCA_TELEGRAM_CHAT_ID` disponíveis como variáveis de ambiente locais
  para teste manual.

## Cenários de validação (sem depender do contrato real da API)

1. **Primeiro mês registrado (sem baseline)**
   - Rodar `src/ipca/fluxo.py` com `estado.json` sem a chave `ultimo_ipca`,
     usando uma fixture simulada.
   - Esperado: notificação enviada com o número do mês e leitura de
     impacto; `estado.json` atualizado.

2. **Novo mês (variação acelerou e acima da meta)**
   - Rodar com `estado.json` já contendo um mês anterior e fixture com mês
     novo e variação maior.
   - Esperado: notificação com `direcao_vs_mes_anterior: acelerou` e
     `posicao_vs_meta` calculada corretamente contra a constante de meta.

3. **Mesmo mês relido (idempotência)**
   - Rodar novamente com a mesma fixture do cenário 2.
   - Esperado: nenhuma notificação; `estado.json` inalterado.

4. **Falha isolada**
   - Forçar uma exceção na leitura da série (ex.: mockar timeout).
   - Esperado: aviso de falha ao bot do fluxo IPCA; `estado.json`
     inalterado; outros dois fluxos não afetados.

## Cenário com API real (após contrato resolvido)

5. **Chamada real à série 433**
   - Rodar `src/ipca/cliente_sgs.py` contra a API real e confirmar que o
     parser extrai `mes_referencia` e `variacao_mensal` conforme
     `contracts/ipca-sgs.md`.
   - Esperado: nenhuma exceção de parsing; valor plausível (variação
     mensal dentro de faixa razoável, ex.: -1% a 3%).
