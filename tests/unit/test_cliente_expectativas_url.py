"""Regressão de produção: a API OData do BCB retorna 400 Bad Request se
espaços forem codificados como '+' (padrão do requests.params) em vez de
'%20'. Ver contracts/focus-api.md e o commit que corrigiu T030."""

from src.focus.cliente_expectativas import _montar_url


def test_montar_url_usa_percent20_em_vez_de_mais():
    url = _montar_url({"$filter": "Indicador eq 'Selic'", "$orderby": "Data desc"})

    assert "+" not in url
    assert "%20" in url


def test_montar_url_codifica_aspas_simples():
    url = _montar_url({"$filter": "Data eq '2026-06-26'"})

    assert "%27" in url
