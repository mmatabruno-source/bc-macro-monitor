import json
from unittest.mock import patch

import pytest

from src.focus.comparador import DivulgacaoFocus
from src.focus.fluxo import processar


@pytest.fixture
def estado_path(tmp_path, monkeypatch):
    caminho = tmp_path / "estado.json"
    caminho.write_text("{}")
    monkeypatch.setattr("src.comum.estado.ESTADO_PATH", caminho)
    monkeypatch.setattr("src.focus.fluxo.ESTADO_PATH", caminho)
    monkeypatch.setenv("FOCUS_TELEGRAM_BOT_TOKEN", "token-fake")
    monkeypatch.setenv("FOCUS_TELEGRAM_CHAT_ID", "chat-fake")
    return caminho


def test_primeira_divulgacao_notifica_sem_direcao(estado_path):
    atual = DivulgacaoFocus(reuniao_id="R5/2026", data_referencia="2026-06-26", mediana_selic=14.0)

    with patch("src.focus.fluxo.buscar_proxima_reuniao", return_value=atual), \
         patch("src.focus.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is True
    mock_enviar.assert_called_once()
    texto_enviado = mock_enviar.call_args.args[0]
    assert "R5/2026" in texto_enviado
    assert "14.0" in texto_enviado

    dados = json.loads(estado_path.read_text())
    assert dados["ultima_expectativa_copom"]["data_referencia"] == "2026-06-26"


def test_nova_divulgacao_mesma_reuniao_notifica_com_direcao(estado_path):
    estado_path.write_text(json.dumps({
        "ultima_expectativa_copom": {
            "reuniao_id": "R5/2026",
            "data_referencia": "2026-06-26",
            "mediana_selic": 14.0,
        }
    }))
    atual = DivulgacaoFocus(reuniao_id="R5/2026", data_referencia="2026-07-03", mediana_selic=14.25)

    with patch("src.focus.fluxo.buscar_proxima_reuniao", return_value=atual), \
         patch("src.focus.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is True
    texto_enviado = mock_enviar.call_args.args[0]
    assert "subiu" in texto_enviado.lower()


def test_mesma_divulgacao_relida_nao_notifica_idempotencia(estado_path):
    estado_path.write_text(json.dumps({
        "ultima_expectativa_copom": {
            "reuniao_id": "R5/2026",
            "data_referencia": "2026-06-26",
            "mediana_selic": 14.0,
        }
    }))
    atual = DivulgacaoFocus(reuniao_id="R5/2026", data_referencia="2026-06-26", mediana_selic=14.0)

    with patch("src.focus.fluxo.buscar_proxima_reuniao", return_value=atual), \
         patch("src.focus.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is False
    mock_enviar.assert_not_called()


def test_troca_de_reuniao_notifica_sem_comparacao_numerica(estado_path):
    """US2: reunião anteriormente monitorada já ocorreu; API retorna a próxima
    reunião real. Notificação deve ser informativa (inicial), sem comparar
    valores numéricos entre reuniões distintas."""
    estado_path.write_text(json.dumps({
        "ultima_expectativa_copom": {
            "reuniao_id": "R4/2026",
            "data_referencia": "2026-05-20",
            "mediana_selic": 14.5,
        }
    }))
    atual = DivulgacaoFocus(reuniao_id="R5/2026", data_referencia="2026-06-26", mediana_selic=14.0)

    with patch("src.focus.fluxo.buscar_proxima_reuniao", return_value=atual), \
         patch("src.focus.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is True
    texto_enviado = mock_enviar.call_args.args[0]
    assert "R5/2026" in texto_enviado
    assert "subiu" not in texto_enviado.lower()
    assert "desceu" not in texto_enviado.lower()
    assert "Mediana anterior" not in texto_enviado

    dados = json.loads(estado_path.read_text())
    assert dados["ultima_expectativa_copom"]["reuniao_id"] == "R5/2026"
