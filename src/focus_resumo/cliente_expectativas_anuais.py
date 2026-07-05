"""Cliente HTTP do endpoint ExpectativasMercadoAnuais (Focus), conforme
specs/004-focus-resumo-semanal/contracts/expectativas-anuais.md (verificado com payload real)."""

from datetime import datetime
from urllib.parse import quote, urlencode

from src.comum.http_retry import requisitar_com_retry
from src.focus_resumo.modelos import DivulgacaoFocusResumo, ValorIndicadorAno

BASE_URL = (
    "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/"
    "ExpectativasMercadoAnuais"
)

INDICADORES = ("IPCA", "Selic", "Câmbio", "PIB Total")


def _montar_url(params):
    # Mesma correção de produção do fluxo 001 (T030): requests.params
    # codifica espaço como '+', mas a API OData exige '%20'.
    query = urlencode(params, quote_via=quote)
    return f"{BASE_URL}?{query}"


def _anos_padrao():
    ano_corrente = datetime.now().year
    return [str(ano_corrente + offset) for offset in range(4)]


def _parse_valores(linhas, anos):
    anos_set = set(anos)
    valores = [
        ValorIndicadorAno(
            indicador=linha["Indicador"],
            ano=linha["DataReferencia"],
            valor=linha["Mediana"],
        )
        for linha in linhas
        if linha["Indicador"] in INDICADORES
        and linha["baseCalculo"] == 0
        and linha["DataReferencia"] in anos_set
    ]
    return valores


def _data_mais_recente():
    url = _montar_url({
        "$filter": "Indicador eq 'IPCA'",
        "$orderby": "Data desc",
        "$top": "1",
        "$format": "json",
    })
    resposta = requisitar_com_retry("GET", url)
    resposta.raise_for_status()
    linhas = resposta.json()["value"]
    return linhas[0]["Data"]


def buscar_resumo_atual():
    """Consulta a API e retorna a DivulgacaoFocusResumo mais recente, com
    os 4 indicadores para o ano corrente + 3 seguintes."""
    data_referencia = _data_mais_recente()
    anos = _anos_padrao()

    filtro_indicadores = " or ".join(f"Indicador eq '{ind}'" for ind in INDICADORES)
    url = _montar_url({
        "$filter": f"Data eq '{data_referencia}' and ({filtro_indicadores})",
        "$format": "json",
    })
    resposta = requisitar_com_retry("GET", url)
    resposta.raise_for_status()
    linhas = resposta.json()["value"]

    valores = _parse_valores(linhas, anos)
    return DivulgacaoFocusResumo(data_referencia=data_referencia, valores=valores)
