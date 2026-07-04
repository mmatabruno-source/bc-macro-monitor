"""Cliente HTTP da API de Agregados (v3) do IBGE, tabela 7060 (composição do
IPCA por grupo).

Não existe API do BC com essa abertura (só a variação geral, série SGS 433)
— quem calcula e publica a composição por grupo, com peso, é o IBGE.

Usa servicodados.ibge.gov.br (API v3), não apisidra.ibge.gov.br: o domínio
apisidra dá connect timeout a partir de IPs de datacenter (confirmado em
teste real no GitHub Actions — funciona de IP residencial, mas não daqui),
enquanto servicodados respondeu normalmente (200, ~1s).
"""

from src.comum.http_retry import requisitar_com_retry
from src.ipca.modelos import GrupoIpca

CODIGO_INDICE_GERAL = "7169"

# Ordem oficial dos 9 grupos do IPCA (código da tabela 7060 -> nome).
CODIGOS_GRUPOS = {
    "7170": "Alimentação e bebidas",
    "7445": "Habitação",
    "7486": "Artigos de residência",
    "7558": "Vestuário",
    "7625": "Transportes",
    "7660": "Saúde e cuidados pessoais",
    "7712": "Despesas pessoais",
    "7766": "Educação",
    "7786": "Comunicação",
}

BASE_URL = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/7060/periodos/-1/"
    "variaveis/63|66?localidades=N1[all]&classificacao=315[{codigos}]"
)

# Número oficial (1-9) de cada grupo, usado para ligar item -> grupo pai
# (o primeiro dígito do código de 4 dígitos do item é esse número).
NUMERO_GRUPO = {
    "Alimentação e bebidas": 1,
    "Habitação": 2,
    "Artigos de residência": 3,
    "Vestuário": 4,
    "Transportes": 5,
    "Saúde e cuidados pessoais": 6,
    "Despesas pessoais": 7,
    "Educação": 8,
    "Comunicação": 9,
}


def _parse_mes_referencia(codigo_periodo):
    # "202605" -> "2026-05"
    return f"{codigo_periodo[:4]}-{codigo_periodo[4:]}"


def _parse_payload(payload):
    """Recebe o payload bruto da API v3 (uma entrada por variável, cada uma
    com um resultado por classificação/grupo) e retorna
    (mes_referencia, variacao_indice_geral, [GrupoIpca, ...])."""
    valores = {}
    mes_referencia = None

    for variavel in payload:
        var_id = variavel["id"]
        for resultado in variavel["resultados"]:
            codigo = next(iter(resultado["classificacoes"][0]["categoria"]))
            serie = resultado["series"][0]["serie"]
            codigo_periodo, valor = next(iter(serie.items()))
            mes_referencia = _parse_mes_referencia(codigo_periodo)
            valores.setdefault(codigo, {})[var_id] = float(valor)

    variacao_indice_geral = valores[CODIGO_INDICE_GERAL]["63"]
    grupos = [
        GrupoIpca(
            nome=nome,
            variacao_mensal=valores[codigo]["63"],
            peso_mensal=valores[codigo]["66"],
        )
        for codigo, nome in CODIGOS_GRUPOS.items()
    ]

    return mes_referencia, variacao_indice_geral, grupos


def buscar_composicao_ipca():
    """Retorna (mes_referencia, variacao_indice_geral, [GrupoIpca, ...]),
    na ordem oficial dos 9 grupos do IPCA."""
    codigos = ",".join([CODIGO_INDICE_GERAL] + list(CODIGOS_GRUPOS))
    url = BASE_URL.format(codigos=codigos)

    resposta = requisitar_com_retry("GET", url, timeout=20)
    resposta.raise_for_status()
    return _parse_payload(resposta.json())


def _nivel_e_nome(d4n_completo):
    """'1101.Cereais, leguminosas e oleaginosas' -> (4, 'Cereais, leguminosas e oleaginosas').
    Retorna (None, texto) para linhas sem prefixo numérico (ex.: 'Índice geral')."""
    prefixo, ponto, nome = d4n_completo.partition(".")
    if ponto and prefixo.isdigit():
        return len(prefixo), nome
    return None, d4n_completo


def _parse_payload_itens(payload):
    """Recebe o payload bruto da API v3 com TODOS os níveis (classificacao
    315/all) e retorna (mes_referencia, {numero_grupo: [GrupoIpca, ...]}) só
    com as linhas de nível 'item' (4 dígitos no D4N)."""
    valores = {}   # codigo -> {var_id: valor}
    nomes = {}     # codigo -> "d4n completo com prefixo"
    mes_referencia = None

    for variavel in payload:
        var_id = variavel["id"]
        for resultado in variavel["resultados"]:
            codigo, nome_completo = next(iter(resultado["classificacoes"][0]["categoria"].items()))
            serie = resultado["series"][0]["serie"]
            codigo_periodo, valor = next(iter(serie.items()))
            mes_referencia = _parse_mes_referencia(codigo_periodo)
            valores.setdefault(codigo, {})[var_id] = float(valor)
            nomes[codigo] = nome_completo

    itens_por_grupo = {n: [] for n in NUMERO_GRUPO.values()}
    for codigo, nome_completo in nomes.items():
        nivel, nome = _nivel_e_nome(nome_completo)
        if nivel != 4:
            continue
        if "63" not in valores.get(codigo, {}) or "66" not in valores.get(codigo, {}):
            continue
        numero_grupo = int(nome_completo[0])
        itens_por_grupo.setdefault(numero_grupo, []).append(
            GrupoIpca(nome=nome, variacao_mensal=valores[codigo]["63"], peso_mensal=valores[codigo]["66"])
        )

    return mes_referencia, itens_por_grupo


def buscar_itens_por_grupo():
    """Retorna (mes_referencia, {numero_grupo: [GrupoIpca, ...]}) com os itens
    (nível 4 dígitos) de todos os grupos, numa chamada separada da
    composição por grupo (ver buscar_composicao_ipca)."""
    url = BASE_URL.format(codigos="all")
    resposta = requisitar_com_retry("GET", url, timeout=20)
    resposta.raise_for_status()
    return _parse_payload_itens(resposta.json())
