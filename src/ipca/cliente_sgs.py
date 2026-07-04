"""Cliente HTTP da série 433 do SGS (IPCA mensal), conforme
specs/003-ipca-mensal/contracts/ipca-sgs.md (verificado com payload real)."""

from src.comum.http_retry import requisitar_com_retry
from src.ipca.modelos import DivulgacaoIpca

BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados/ultimos/{n}"


def _parse_mes_referencia(data):
    # "DD/MM/YYYY" (DD sempre "01") -> "YYYY-MM"
    _dia, mes, ano = data.split("/")
    return f"{ano}-{mes}"


def _parse_divulgacoes(payload):
    return [
        DivulgacaoIpca(
            mes_referencia=_parse_mes_referencia(item["data"]),
            variacao_mensal=float(item["valor"]),
        )
        for item in payload
    ]


def buscar_ultimas_divulgacoes(quantidade=2):
    """Retorna as `quantidade` divulgações mais recentes, ordenadas do mais
    antigo para o mais recente (último elemento = mês mais recente)."""
    resposta = requisitar_com_retry(
        "GET",
        BASE_URL.format(n=quantidade),
        params={"formato": "json"},
    )
    resposta.raise_for_status()
    return _parse_divulgacoes(resposta.json())
