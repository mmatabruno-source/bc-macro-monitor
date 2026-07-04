"""Cliente HTTP da série 432 do SGS (Meta Selic vigente definida pelo Copom)."""

from src.comum.http_retry import requisitar_com_retry

BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1"


def buscar_selic_vigente():
    """Retorna a meta Selic vigente (a.a.), conforme a última decisão do Copom."""
    resposta = requisitar_com_retry("GET", BASE_URL, params={"formato": "json"})
    resposta.raise_for_status()
    return float(resposta.json()[0]["valor"])
