# Contrato: Série 433 do SGS (IPCA mensal) — BLOQUEADO

**Status**: 🔴 **NÃO VERIFICADO. Não usar para implementação.**

Por Princípio II da constituição, este arquivo não pode conter um schema
de campos até que o payload real de uma chamada de teste seja fornecido
pelo usuário.

## O que falta

Colar aqui (ou em mensagem para o agente) a resposta real de:

```
https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados/ultimos/3?formato=json
```

(3 últimos valores, para já observar pelo menos uma transição de mês).

## O que este contrato precisa documentar assim que o payload chegar

- Nome exato dos campos que contêm a data/mês de referência e o valor da
  variação mensal.
- Formato de data (ISO 8601? `dd/mm/yyyy`?).
- Formato do valor (string ou número? separador decimal?).
- Comportamento ao pedir mais registros (`ultimos/N` com N maior) e se há
  paginação.
- Códigos de status HTTP observados e formato de erro, se algum foi
  testado.

## Tarefas bloqueadas por este contrato

Todas as tarefas de implementação de `src/ipca/cliente_sgs.py` e
`tests/contract/test_contrato_ipca.py` em `tasks.md` ficam bloqueadas até
este arquivo ser preenchido a partir de um payload real.
