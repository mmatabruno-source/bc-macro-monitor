from src.ipca.leitura_impacto import calcular_variacao_anualizada


def test_calcula_variacao_anualizada_juros_compostos():
    # (1,0058)^12 - 1 ≈ 7,1893% (não 0,58*12=6,96%, que seria juros simples)
    resultado = calcular_variacao_anualizada(0.58)

    assert round(resultado, 4) == round(((1.0058) ** 12 - 1) * 100, 4)
    assert resultado > 0.58 * 12  # composto sempre >= simples para valores positivos


def test_variacao_anualizada_zero():
    assert calcular_variacao_anualizada(0.0) == 0.0


def test_variacao_anualizada_negativa():
    resultado = calcular_variacao_anualizada(-0.5)

    assert round(resultado, 4) == round(((0.995) ** 12 - 1) * 100, 4)
    assert resultado < 0
