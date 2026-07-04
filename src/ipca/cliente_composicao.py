"""Cliente HTTP da tabela SIDRA 7060 do IBGE (composição do IPCA por grupo).

Não existe API do BC com essa abertura (só a variação geral, série SGS 433)
— quem calcula e publica a composição por grupo, com peso, é o IBGE, via
SIDRA. Ver https://sidra.ibge.gov.br/tabela/7060.
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

BASE_URL = "https://apisidra.ibge.gov.br/values/t/7060/n1/all/v/63,66/p/last%201/c315/{codigos}"


def _parse_mes_referencia(codigo_periodo):
    # "202605" -> "2026-05"
    return f"{codigo_periodo[:4]}-{codigo_periodo[4:]}"


def _parse_payload(payload):
    """Recebe o payload bruto da SIDRA (com cabeçalho na primeira posição) e
    retorna (mes_referencia, variacao_indice_geral, [GrupoIpca, ...])."""
    linhas = payload[1:]  # primeira linha é o cabeçalho de colunas

    mes_referencia = _parse_mes_referencia(linhas[0]["D3C"])
    valores = {}
    for linha in linhas:
        valores.setdefault(linha["D4C"], {})[linha["D2C"]] = float(linha["V"])

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

    resposta = requisitar_com_retry("GET", url, params={"formato": "json"}, timeout=20)
    resposta.raise_for_status()
    return _parse_payload(resposta.json())
