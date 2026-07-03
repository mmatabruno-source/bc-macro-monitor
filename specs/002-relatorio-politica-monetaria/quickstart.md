# Quickstart: Validação do Fluxo Relatório de Política Monetária

## Pré-requisitos

- Python 3.12 instalado.
- Payload real do dataset fornecido, `contracts/relatorio-dataset.md`
  preenchido, e decisão PDF-vs-estruturado tomada (bloqueios do Princípio
  II resolvidos) — sem isso, só os cenários 1–3 abaixo (fixtures
  simuladas, sem extração de conteúdo real) podem ser executados.
- Bot do Telegram dedicado ao fluxo Relatório criado, com
  `RELATORIO_TELEGRAM_BOT_TOKEN` e `RELATORIO_TELEGRAM_CHAT_ID`
  disponíveis como variáveis de ambiente locais.
- Se a decisão de research.md exigir LLM: chave de API correspondente
  disponível localmente para teste (nunca commitada).

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

## Cenário com dataset/conteúdo real (após contrato e decisão resolvidos)

4. **Chamada real ao dataset e extração do conteúdo**
   - Rodar `src/relatorio/cliente_dataset.py` e `src/relatorio/extrator_conteudo.py`
     contra os dados reais e confirmar que a sequência completa de 4
     mensagens é gerada corretamente para o relatório mais recente
     publicado.
