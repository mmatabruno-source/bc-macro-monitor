from src.focus.comparador import calcular_variacao


def test_variacao_negativa_corte_projetado():
    variacao, emoji = calcular_variacao(selic_vigente=14.25, mediana_projetada=14.0)

    assert variacao == -0.25
    assert emoji == "📉"


def test_variacao_positiva_alta_projetada():
    variacao, emoji = calcular_variacao(selic_vigente=14.25, mediana_projetada=14.5)

    assert variacao == 0.25
    assert emoji == "📈"


def test_variacao_zero_estabilidade_projetada():
    variacao, emoji = calcular_variacao(selic_vigente=14.25, mediana_projetada=14.25)

    assert variacao == 0
    assert emoji == "➡️"
