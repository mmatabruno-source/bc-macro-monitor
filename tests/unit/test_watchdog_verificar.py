from datetime import datetime, timedelta, timezone

from src.watchdog.verificar import avaliar_execucoes

AGORA = datetime(2026, 7, 6, 12, 50, tzinfo=timezone.utc)


def _execucao(horas_atras, conclusion="success"):
    data = AGORA - timedelta(hours=horas_atras)
    return {"conclusion": conclusion, "created_at": data.isoformat().replace("+00:00", "Z")}


def test_lista_vazia_nunca_alerta():
    deve_alertar, motivo = avaliar_execucoes([], agora=AGORA)

    assert deve_alertar is False
    assert motivo is None


def test_execucao_recente_e_saudavel_nao_alerta():
    execucoes = [_execucao(1), _execucao(25), _execucao(49)]

    deve_alertar, motivo = avaliar_execucoes(execucoes, agora=AGORA)

    assert deve_alertar is False
    assert motivo is None


def test_execucao_mais_recente_muito_antiga_alerta():
    execucoes = [_execucao(31), _execucao(55)]

    deve_alertar, motivo = avaliar_execucoes(execucoes, agora=AGORA)

    assert deve_alertar is True
    assert "últimas 30h" in motivo


def test_tres_falhas_consecutivas_alertam_mesmo_com_execucao_recente():
    execucoes = [
        _execucao(1, "failure"),
        _execucao(25, "failure"),
        _execucao(49, "failure"),
        _execucao(73, "success"),
    ]

    deve_alertar, motivo = avaliar_execucoes(execucoes, agora=AGORA)

    assert deve_alertar is True
    assert "3 execuções" in motivo


def test_falhas_intercaladas_com_sucesso_nao_alertam():
    execucoes = [_execucao(1, "failure"), _execucao(25, "success"), _execucao(49, "failure")]

    deve_alertar, motivo = avaliar_execucoes(execucoes, agora=AGORA)

    assert deve_alertar is False
    assert motivo is None


def test_menos_execucoes_que_o_limite_de_falhas_nao_alerta_por_falha():
    execucoes = [_execucao(1, "failure"), _execucao(25, "failure")]

    deve_alertar, motivo = avaliar_execucoes(execucoes, agora=AGORA)

    assert deve_alertar is False
    assert motivo is None
