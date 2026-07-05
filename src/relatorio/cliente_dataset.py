"""Cliente HTTP do dataset de Relatórios de Política Monetária, conforme
specs/002-relatorio-politica-monetaria/contracts/relatorio-dataset.md
(verificado com payload real).

O relatório foi renomeado de "Relatório de Inflação" para "Relatório de
Política Monetária" (RPM) a partir da edição 202503; o dataset antigo
(`ri/relatorios`) parou de receber itens novos e ficou parado em 202412
(a última edição sob o nome antigo) — descoberto em produção quando o
fluxo continuou "avisando" sobre o mesmo relatório de dez/2024 mesmo
meses depois. O dataset novo (`rpm/relatorios`) tem o mesmo schema."""

from src.comum.http_retry import requisitar_com_retry
from src.relatorio.modelos import RelatorioPoliticaMonetaria

BASE_URL = "https://www.bcb.gov.br/api/servico/sitebcb/rpm/relatorios"


def _parse_relatorios(payload):
    return [
        RelatorioPoliticaMonetaria(
            identificador=item["identificador"],
            data_publicacao=item["dataReferencia"],
            link_pdf=item["url"],
            link_pagina=item["linkPaginaBC"],
        )
        for item in payload["conteudo"]
    ]


def buscar_relatorio_mais_recente():
    """Retorna o RelatorioPoliticaMonetaria mais recente (primeiro elemento
    de `conteudo`, conforme Regra de ordenação do contrato)."""
    resposta = requisitar_com_retry("GET", BASE_URL, params={"quantidade": "1"})
    resposta.raise_for_status()
    relatorios = _parse_relatorios(resposta.json())
    return relatorios[0]
