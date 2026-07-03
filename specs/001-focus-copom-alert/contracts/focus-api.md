# Contrato: API de Expectativas de Mercado (Focus) — BLOQUEADO

**Status**: 🔴 **NÃO VERIFICADO. Não usar para implementação.**

Por Princípio II da constituição deste projeto ("Nunca Codificar Contra um
Contrato de API Não Verificado"), este arquivo **não pode** conter um
schema de campos até que o payload real de uma chamada de teste seja
fornecido pelo usuário.

## O que falta

O usuário precisa colar aqui (ou em mensagem para o agente, que então
preenche este arquivo) a resposta JSON real de uma chamada de teste ao
endpoint candidato:

```
https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/...
```

(serviço `ExpectativasMercadoSelic`), obtida via navegador, curl ou
Postman, filtrando pela reunião de Copom mais próxima.

## O que este contrato precisa documentar assim que o payload chegar

- Nome exato dos campos que contêm: identificador/data da reunião do
  Copom, data de referência da divulgação/pesquisa Focus, e o valor da
  mediana da Selic esperada.
- Formato de datas (ISO 8601? `dd/mm/yyyy`? timestamp?).
- Se a resposta retorna uma única reunião "próxima" ou uma lista de
  reuniões futuras que precisa ser filtrada pelo cliente.
- Códigos de status HTTP observados e formato de erro, se algum foi
  testado.
- Paginação, se houver (`$top`, `$skip` no padrão OData).

## Tarefas bloqueadas por este contrato

Todas as tarefas de implementação de `src/focus/cliente_expectativas.py` e
`tests/contract/test_contrato_focus.py` em `tasks.md` ficam bloqueadas até
este arquivo ser preenchido a partir de um payload real.
