import json
from datetime import datetime
from unittest.mock import patch

import pytest

from src.comum.isolamento import _executar_isolado
from src.lembrete_calendario_copom.fluxo import processar


@pytest.fixture
def estado_path(tmp_path, monkeypatch):
    caminho = tmp_path / "estado.json"
    caminho.write_text("{}")
    monkeypatch.setattr("src.comum.estado.ESTADO_PATH", caminho)
    monkeypatch.setattr("src.lembrete_calendario_copom.fluxo.ESTADO_PATH", caminho)
    monkeypatch.setenv("FOCUS_TELEGRAM_BOT_TOKEN", "token-fake")
    monkeypatch.setenv("FOCUS_TELEGRAM_CHAT_ID", "chat-fake")
    return caminho


def _mock_datetime_ano(ano):
    class _DatetimeFake(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(ano, 7, 31)
    return _DatetimeFake


def test_antes_de_2027_nao_envia(estado_path):
    with patch("src.lembrete_calendario_copom.fluxo.datetime", _mock_datetime_ano(2026)), \
         patch("src.lembrete_calendario_copom.fluxo.enviar_mensagem") as mock_enviar:
        enviado = processar()

    assert enviado is False
    mock_enviar.assert_not_called()
    assert json.loads(estado_path.read_text()) == {}


def test_em_2027_envia_lembrete_do_ano_seguinte(estado_path):
    with patch("src.lembrete_calendario_copom.fluxo.datetime", _mock_datetime_ano(2027)), \
         patch("src.lembrete_calendario_copom.fluxo.enviar_mensagem") as mock_enviar:
        enviado = processar()

    assert enviado is True
    mock_enviar.assert_called_once()
    texto = mock_enviar.call_args.args[0]
    assert "2028" in texto
    assert "calendario_copom.py" in texto

    dados = json.loads(estado_path.read_text())
    assert dados["ultimo_lembrete_calendario_copom"]["ano"] == 2027


def test_mesmo_ano_relido_nao_reenvia(estado_path):
    estado_path.write_text(json.dumps({"ultimo_lembrete_calendario_copom": {"ano": 2027}}))

    with patch("src.lembrete_calendario_copom.fluxo.datetime", _mock_datetime_ano(2027)), \
         patch("src.lembrete_calendario_copom.fluxo.enviar_mensagem") as mock_enviar:
        enviado = processar()

    assert enviado is False
    mock_enviar.assert_not_called()


def test_falha_no_envio_nao_grava_estado(estado_path):
    estado_original = estado_path.read_text()

    with patch("src.lembrete_calendario_copom.fluxo.datetime", _mock_datetime_ano(2027)), \
         patch("src.lembrete_calendario_copom.fluxo.enviar_mensagem", side_effect=RuntimeError("Telegram fora do ar")):
        resultado = _executar_isolado("Lembrete Calendário Copom", processar)

    assert resultado["falhou"] is True
    assert estado_path.read_text() == estado_original
