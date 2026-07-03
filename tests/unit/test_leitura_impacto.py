from src.ipca.leitura_impacto import META_INFLACAO_CENTRO, gerar_leitura
from src.ipca.modelos import DivulgacaoIpca


def _divulgacao(mes, valor):
    return DivulgacaoIpca(mes_referencia=mes, variacao_mensal=valor)


def test_acelerou_vs_mes_anterior():
    anterior = _divulgacao("2026-04", 0.5)
    atual = _divulgacao("2026-05", 0.7)

    leitura = gerar_leitura(anterior, atual)

    assert leitura.direcao_vs_mes_anterior == "acelerou"


def test_desacelerou_vs_mes_anterior():
    anterior = _divulgacao("2026-04", 0.7)
    atual = _divulgacao("2026-05", 0.5)

    leitura = gerar_leitura(anterior, atual)

    assert leitura.direcao_vs_mes_anterior == "desacelerou"


def test_estavel_vs_mes_anterior():
    anterior = _divulgacao("2026-04", 0.5)
    atual = _divulgacao("2026-05", 0.5)

    leitura = gerar_leitura(anterior, atual)

    assert leitura.direcao_vs_mes_anterior == "estavel"


def test_acima_da_meta():
    # anualizado = 0.5 * 12 = 6.0%, acima do centro de META_INFLACAO_CENTRO
    anterior = _divulgacao("2026-04", 0.5)
    atual = _divulgacao("2026-05", 0.5)
    assert META_INFLACAO_CENTRO < 6.0

    leitura = gerar_leitura(anterior, atual)

    assert leitura.posicao_vs_meta == "acima"


def test_abaixo_da_meta():
    # anualizado = 0.1 * 12 = 1.2%, abaixo do centro
    anterior = _divulgacao("2026-04", 0.1)
    atual = _divulgacao("2026-05", 0.1)
    assert META_INFLACAO_CENTRO > 1.2

    leitura = gerar_leitura(anterior, atual)

    assert leitura.posicao_vs_meta == "abaixo"
