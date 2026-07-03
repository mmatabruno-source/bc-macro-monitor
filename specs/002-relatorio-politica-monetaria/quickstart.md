# Quickstart: Validação do Fluxo Relatório de Política Monetária

## Pré-requisitos

- Python 3.12 instalado, com `anthropic` no `requirements.txt`.
- Bot do Telegram dedicado ao fluxo Relatório criado, com
  `RELATORIO_TELEGRAM_BOT_TOKEN` e `RELATORIO_TELEGRAM_CHAT_ID`
  disponíveis como variáveis de ambiente locais.
- `ANTHROPIC_API_KEY` disponível localmente para o cenário 4 (chamada real
  à Claude API com PDF) — nunca commitada.

## Cenários de validação (sem depender do contrato real)

1. **Novo relatório detectado, análise completa gerada com sucesso**
   - Rodar `src/relatorio/fluxo.py` com `estado.json` sem `ultimo_relatorio`,
     usando uma fixture simulada com conteúdo completo.
   - Esperado: sequência de 4 mensagens enviada (aviso, cenário, projeções,
     portfólio); `estado.json` atualizado após confirmação.

2. **Relatório já processado (idempotência)**
   - Rodar novamente com a mesma fixture do cenário 1.
   - Esperado: nenhuma notificação; `estado.json` inalterado.

3. **Falha na geração da análise crítica (fallback FR-006)**
   - Forçar uma exceção na extração/geração de conteúdo, mantendo a
     detecção do relatório novo intacta.
   - Esperado: ao menos a mensagem de aviso de publicação com link é
     enviada; a falha de análise é tratada como falha isolada (aviso ao
     bot do fluxo Relatório), sem impedir os outros dois fluxos.

## Cenário com dataset/API real

4. **Chamada real ao dataset e à Claude API**
   - Rodar `src/relatorio/cliente_dataset.py` e `src/relatorio/gerador_analise.py`
     contra os dados reais (dataset + PDF + Claude API) e confirmar que a
     sequência completa de 4 mensagens é gerada corretamente para o
     relatório mais recente publicado.
