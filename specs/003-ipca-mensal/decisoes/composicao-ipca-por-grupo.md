# Decisão: composição do IPCA por grupo (variação + peso) na mensagem do fluxo

**Data**: 2026-07-04
**Status**: ✅ Decidido e implementado (com fallback).

## Contexto / pedido original

A mensagem original do fluxo IPCA só trazia a variação mensal geral e uma
leitura de impacto (`📈 IPCA — 2026-05 / Variação mensal: 0.58% / Leitura:
desacelerou..., acima da meta`). O usuário considerou isso pouco útil
sozinho e pediu a composição por grupo (os 9 grupos oficiais do IPCA:
Alimentação e bebidas, Habitação, Artigos de residência, Vestuário,
Transportes, Saúde e cuidados pessoais, Despesas pessoais, Educação,
Comunicação), com variação % e peso % de cada um, substituindo (não
complementando com um novo fluxo) a mensagem existente.

## Por que não dá para usar a API do Banco Central

O SGS do BC (`api.bcb.gov.br/dados/serie/...`) só tem séries agregadas
(ex.: a 433, usada pelo IPCA geral). Não existe série "por grupo" no
catálogo do BC — essa abertura é calculada e publicada só pelo IBGE.

## Fontes candidatas testadas (todas com chamadas reais, não hipóteses)

### 1. `apisidra.ibge.gov.br` (API SIDRA "values", formato legado)

- Tabela 7060 do IBGE tem exatamente o que precisamos: variação mensal
  (variável 63) e peso mensal (variável 66), por grupo/subgrupo/item/
  subitem, com histórico desde jan/2020.
- URL testada (sintaxe confirmada correta contra a documentação oficial
  via busca — `t/<tabela>/n<nível>/<códigos>/v/<variáveis>/p/<período>/
  c<classificação>/<categorias>`):
  ```
  https://apisidra.ibge.gov.br/values/t/7060/n1/all/v/63,66/p/last%201/c315/7169,7170,7445,7486,7558,7625,7660,7712,7766,7786?formato=json
  ```
- **Funciona perfeitamente de rede residencial** (o usuário testou no
  navegador e recebeu o payload completo e correto).
- **Falha sistematicamente do GitHub Actions**: `ConnectTimeout` em
  10/10 tentativas, em duas rodadas de teste diferentes (runs
  `28708943251` região do teste inicial, e testes de confiabilidade
  subsequentes). A conexão TCP nem se estabelece (não é um erro HTTP,
  é timeout de conexão) — descarta hipótese de erro de sintaxe/header.

### 2. `servicodados.ibge.gov.br/api/v3/agregados` (API de Agregados v3, atual)

- Mesma tabela 7060, formato de resposta mais aninhado (array de
  variáveis → resultados → classificações → séries).
- URL testada (sintaxe confirmada via busca e batendo com exemplos
  reais indexados):
  ```
  https://servicodados.ibge.gov.br/api/v3/agregados/7060/periodos/-1/variaveis/63|66?localidades=N1[all]&classificacao=315[7169,7170,7445,7486,7558,7625,7660,7712,7766,7786]
  ```
- É a API que o wrapper Python da comunidade (`sidrapy`) usa
  internamente — evidência de que é o caminho "correto"/recomendado.
- **Resultado real, instável**: numa tentativa (run `28710727605`)
  respondeu `200 OK` com dados corretos em ~1s. Minutos depois (run
  `28710823967`), `ConnectTimeout`. Numa rodada de 5 tentativas
  seguidas (run `28711067581`), 0/5 sucesso. Numa rodada isolada (run
  `28711653696`), voltou a funcionar rápido (~0.17s de conexão raw,
  confirmado via socket direto). **Sem padrão previsível.**

### 3. `www.ipeadata.gov.br/api/odata4` (IPEADATA, infraestrutura separada do IBGE)

- Espelha várias séries do IBGE/BC; tem API OData4 própria.
- **Não confirmado se tem peso mensal por grupo** (o catálogo padrão do
  IPEADATA tende a focar em variação/índice, não peso — não validamos
  isso por não termos conseguido nem passar da etapa de sintaxe).
- Testamos 10+ variantes de sintaxe de `$filter` na entidade `Metadados`
  (aspas simples/duplas, `contains`/`substringof`/`startswith`, com e
  sem `$select`/`$top`, com e sem URL-encoding manual vs. via dict
  `params=` do `requests`, replicando literalmente exemplos de projetos
  reais no GitHub — `igorpdev/databr`, `robertoecf/OpenFinData`,
  `nferdica/brazil-visible`). **Todas retornaram `400 The query
  specified in the URI is not valid.`** quando a conexão em si
  funcionava.
- E quando tentamos confirmar o schema real via `GET /$metadata` (para
  descartar a hipótese de nome de campo errado), a conexão deu
  `ConnectTimeout` — ou seja, a mesma instabilidade de rede também
  afeta esse domínio, independente do IBGE.
- **Abandonado**: nem a sintaxe foi validada, nem a disponibilidade do
  campo peso, e sofre da mesma instabilidade de conexão.

## Diagnósticos que descartaram hipóteses de "bug nosso"

- **Sintaxe de URL**: confirmada correta para as 2 APIs do IBGE contra
  documentação oficial (indexada via busca — o WebFetch direto em
  qualquer domínio `.gov.br`, incluindo páginas do BC que sabemos que
  funcionam via HTTP puro, retorna 403 nesse ambiente; é bloqueio
  genérico de scraping do lado do proxy daqui, não evidência sobre o
  IBGE especificamente).
- **IPv4 vs IPv6**: testado com socket raw. Nenhum dos 3 domínios tem
  registro `AAAA` (só IPv4) — não há rota IPv6 quebrada para evitar. A
  conexão IPv4 direta funcionou rápido nesse teste específico (mas
  falhou em outras rodadas), reforçando que é instabilidade
  intermitente, não um problema de família de IP.
- **Timeout curto demais**: testado com timeout de até 20s por
  tentativa — nas rodadas de falha, os 3 domínios deram timeout mesmo
  assim (não é questão de esperar mais um pouco).
- **Retry insuficiente**: `requisitar_com_retry` (`src/comum/http_retry.py`)
  já faz 3 tentativas com backoff — mas quando a instabilidade dura
  minutos (como observado), retries dentro de uma única execução do
  workflow (segundos a poucos minutos de janela) não são garantia de
  sucesso.

## Conclusão

Isso não é um bug de implementação, nem escolha errada de API, nem
sintaxe incorreta. É instabilidade de rede real e imprevisível entre o
range de IP dos runners hospedados do GitHub Actions (datacenter
Azure) e a infraestrutura de pelo menos 3 domínios `.gov.br`
diferentes. Não há evidência pública (buscada e não encontrada) de que
outros desenvolvedores documentaram esse padrão especificamente — é uma
observação empírica própria deste projeto.

## Decisão final

1. **Fonte primária**: `servicodados.ibge.gov.br` (API v3 de Agregados),
   por ser o padrão recomendado pela comunidade (`sidrapy` usa essa),
   com timeout de 20s (`src/ipca/cliente_composicao.py`).
2. **Fallback obrigatório no fluxo** (`src/ipca/fluxo.py`): se
   `buscar_composicao_ipca()` falhar por qualquer motivo, o fluxo
   envia a mensagem do IPCA **sem** a tabela de composição (só
   variação geral + leitura), e não deixa a exceção propagar e
   bloquear o alerta principal.
3. **Self-hosted runner (IP residencial) foi cogitado e adiado**: é a
   única solução que eliminaria a causa raiz (o padrão observado é
   consistente com bloqueio/degradação específica de ranges de IP de
   datacenter/nuvem — o mesmo aconteceria numa VPS comum tipo
   DigitalOcean/Linode, não só no GitHub Actions). Envolve manter uma
   máquina sempre ligada e risco de segurança se o repo for público
   (PR de fork rodando em runner self-hosted pode expor secrets). O
   usuário já opera self-hosted para outro projeto (monitor do Diário
   Oficial da União), então tem know-how, mas decidiu não migrar agora
   — reavaliar se a taxa de falha em produção real (com o fallback já
   em prática) se mostrar alta demais.

## Runs de teste reais referenciados (para auditoria futura)

Todos no repositório `mmatabruno-source/bc-macro-monitor`, branch
`claude/pending-work-continuation-u29sq7`, workflow `monitor.yml`:
`28708943251`, `28709204669`, `28709464945`, `28709539409`,
`28710433395` (cancelado), `28710565855`, `28710727605`, `28710823967`,
`28711067581`, `28711456955`, `28711653696`, `28711751676`,
`28711926759`, `28712000295`.
