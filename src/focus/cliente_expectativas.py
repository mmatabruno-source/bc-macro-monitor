"""Cliente HTTP do endpoint ExpectativasMercadoSelic (Focus), conforme
specs/001-focus-copom-alert/contracts/focus-api.md (verificado com payload real)."""

from src.comum.http_retry import requisitar_com_retry
from src.focus.comparador import DivulgacaoFocus

BASE_URL = (
    "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/"
    "ExpectativasMercadoSelic"
)


def _parse_reuniao(reuniao_id):
    """'"R5/2026"' -> (2026, 5), para ordenar cronologicamente."""
    numero, ano = reuniao_id.lstrip("R").split("/")
    return int(ano), int(numero)


def _escolher_proxima_reuniao(linhas):
    """Dado um conjunto de linhas da mesma divulgação (mesma Data), com
    baseCalculo=0, escolhe a de menor (ano, número) — Regra 2 do contrato."""
    linhas_base_ampla = [linha for linha in linhas if linha["baseCalculo"] == 0]
    escolhida = min(linhas_base_ampla, key=lambda linha: _parse_reuniao(linha["Reuniao"]))
    return DivulgacaoFocus(
        reuniao_id=escolhida["Reuniao"],
        data_referencia=escolhida["Data"],
        mediana_selic=escolhida["Mediana"],
    )


def _data_mais_recente():
    resposta = requisitar_com_retry(
        "GET",
        BASE_URL,
        params={
            "$filter": "Indicador eq 'Selic'",
            "$orderby": "Data desc",
            "$top": "1",
            "$format": "json",
        },
    )
    resposta.raise_for_status()
    linhas = resposta.json()["value"]
    return linhas[0]["Data"]


def buscar_proxima_reuniao():
    """Consulta a API Focus e retorna a DivulgacaoFocus da próxima reunião
    do Copom, com base na divulgação mais recente disponível."""
    data_referencia = _data_mais_recente()

    resposta = requisitar_com_retry(
        "GET",
        BASE_URL,
        params={
            "$filter": f"Data eq '{data_referencia}' and Indicador eq 'Selic'",
            "$format": "json",
        },
    )
    resposta.raise_for_status()
    linhas = resposta.json()["value"]

    return _escolher_proxima_reuniao(linhas)
