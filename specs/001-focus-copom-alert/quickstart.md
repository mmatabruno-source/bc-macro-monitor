# Quickstart: Validação do Fluxo Focus/Copom

## Pré-requisitos

- Python 3.12 instalado.
- Payload real do endpoint Focus fornecido e `contracts/focus-api.md`
  preenchido (bloqueio do Princípio II resolvido) — sem isso, apenas os
  cenários com dados simulados (fixtures) abaixo podem ser executados.
- Bot do Telegram dedicado ao fluxo Focus criado, com `FOCUS_TELEGRAM_BOT_TOKEN`
  e `FOCUS_TELEGRAM_CHAT_ID` disponíveis como variáveis de ambiente locais
  para teste manual (nunca commitados).

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Cenários de validação (sem depender do contrato real da API)

1. **Primeira divulgação de uma reunião (sem baseline)**
   - Rodar `src/focus/fluxo.py` com `estado.json` sem a chave
     `ultima_expectativa_copom`, usando uma fixture de divulgação simulada.
   - Esperado: notificação informativa (`direcao: inicial`) enviada ao bot
     de teste; `estado.json` atualizado com a nova divulgação.

2. **Nova divulgação da mesma reunião (mediana subiu)**
   - Rodar com `estado.json` já contendo uma divulgação anterior e uma
     fixture com `data_referencia` mais recente e `mediana_selic` maior.
   - Esperado: notificação com `direcao: subiu`, valores anterior e novo
     corretos; `estado.json` atualizado.

3. **Mesma divulgação relida (idempotência)**
   - Rodar novamente com a mesma fixture do cenário 2, sem alterar
     `estado.json` entre as execuções.
   - Esperado: nenhuma notificação enviada; `estado.json` inalterado.

4. **Troca de reunião monitorada**
   - Rodar com `estado.json` apontando para uma `reuniao_id` já passada e
     uma fixture cuja `reuniao_id` é a próxima reunião real.
   - Esperado: notificação informativa (`direcao: inicial`) para a nova
     reunião, sem comparação com o valor da reunião anterior.

5. **Falha isolada**
   - Forçar uma exceção na leitura da API (ex.: mockar timeout).
   - Esperado: aviso de falha enviado ao bot do fluxo Focus;
     `estado.json` não alterado; execução dos outros dois fluxos (simulados
     no mesmo processo principal) não afetada.

## Cenário de validação com API real (após contrato resolvido)

6. **Chamada real ao endpoint Focus**
   - Rodar `src/focus/cliente_expectativas.py` contra a API real e
     confirmar que o parser extrai `reuniao_id`, `data_referencia` e
     `mediana_selic` conforme documentado em `contracts/focus-api.md`.
   - Esperado: nenhuma exceção de parsing; valores plausíveis (mediana
     dentro de faixa razoável da Selic, data de referência recente).
