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
