from src.focus.comparador import DivulgacaoFocus, comparar


def _divulgacao(reuniao_id, data_referencia, mediana_selic):
    return DivulgacaoFocus(
        reuniao_id=reuniao_id,
        data_referencia=data_referencia,
        mediana_selic=mediana_selic,
    )


def test_sem_baseline_retorna_inicial():
    atual = _divulgacao("R5/2026", "2026-07-03", 14.0)

    assert comparar(None, atual) == "inicial"


def test_mediana_subiu():
    anterior = _divulgacao("R5/2026", "2026-06-26", 14.0)
    atual = _divulgacao("R5/2026", "2026-07-03", 14.25)

    assert comparar(anterior, atual) == "subiu"


def test_mediana_desceu():
    anterior = _divulgacao("R5/2026", "2026-06-26", 14.0)
    atual = _divulgacao("R5/2026", "2026-07-03", 13.75)

    assert comparar(anterior, atual) == "desceu"


def test_mediana_manteve():
    anterior = _divulgacao("R5/2026", "2026-06-26", 14.0)
    atual = _divulgacao("R5/2026", "2026-07-03", 14.0)

    assert comparar(anterior, atual) == "manteve"


def test_troca_de_reuniao_retorna_inicial_mesmo_com_baseline():
    anterior = _divulgacao("R4/2026", "2026-05-20", 14.5)
    atual = _divulgacao("R5/2026", "2026-06-26", 14.0)

    assert comparar(anterior, atual) == "inicial"
