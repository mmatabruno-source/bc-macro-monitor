from src.focus_resumo.comparador import comparar_valores
from src.focus_resumo.modelos import ValorIndicadorAno


def test_sem_historico_retorna_none():
    atuais = [ValorIndicadorAno(indicador="Selic", ano="2026", valor=14.0)]

    direcoes = comparar_valores({}, atuais)

    assert direcoes["Selic:2026"] is None


def test_subiu():
    anterior = {"Selic:2026": 13.75}
    atuais = [ValorIndicadorAno(indicador="Selic", ano="2026", valor=14.0)]

    direcoes = comparar_valores(anterior, atuais)

    assert direcoes["Selic:2026"] == "subiu"


def test_desceu():
    anterior = {"Selic:2026": 14.25}
    atuais = [ValorIndicadorAno(indicador="Selic", ano="2026", valor=14.0)]

    direcoes = comparar_valores(anterior, atuais)

    assert direcoes["Selic:2026"] == "desceu"


def test_manteve():
    anterior = {"Selic:2026": 14.0}
    atuais = [ValorIndicadorAno(indicador="Selic", ano="2026", valor=14.0)]

    direcoes = comparar_valores(anterior, atuais)

    assert direcoes["Selic:2026"] == "manteve"


def test_itens_independentes():
    anterior = {"Selic:2026": 14.0}
    atuais = [
        ValorIndicadorAno(indicador="Selic", ano="2026", valor=14.25),
        ValorIndicadorAno(indicador="IPCA", ano="2026", valor=5.33),
    ]

    direcoes = comparar_valores(anterior, atuais)

    assert direcoes["Selic:2026"] == "subiu"
    assert direcoes["IPCA:2026"] is None
