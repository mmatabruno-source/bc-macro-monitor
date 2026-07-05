from unittest.mock import patch

import pytest

from src.watchdog.fluxo import processar


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "mmatabruno-source/bc-macro-monitor")
    monkeypatch.setenv("GITHUB_TOKEN", "token-fake")
    monkeypatch.setenv("WATCHDOG_TELEGRAM_BOT_TOKEN", "bot-fake")
    monkeypatch.setenv("WATCHDOG_TELEGRAM_CHAT_ID", "chat-fake")


def test_lista_vazia_nao_envia_alerta():
    with patch("src.watchdog.fluxo.buscar_execucoes_recentes", return_value=[]), \
         patch("src.watchdog.fluxo.enviar_mensagem") as mock_enviar:
        alertou = processar()

    assert alertou is False
    mock_enviar.assert_not_called()


def test_execucao_saudavel_nao_envia_alerta():
    execucoes = [{"conclusion": "success", "created_at": "2026-07-06T09:20:00Z"}]

    with patch("src.watchdog.fluxo.buscar_execucoes_recentes", return_value=execucoes), \
         patch("src.watchdog.fluxo.avaliar_execucoes", return_value=(False, None)), \
         patch("src.watchdog.fluxo.enviar_mensagem") as mock_enviar:
        alertou = processar()

    assert alertou is False
    mock_enviar.assert_not_called()


def test_problema_detectado_envia_alerta():
    with patch("src.watchdog.fluxo.buscar_execucoes_recentes", return_value=[{}]), \
         patch("src.watchdog.fluxo.avaliar_execucoes", return_value=(True, "motivo de teste")), \
         patch("src.watchdog.fluxo.enviar_mensagem") as mock_enviar:
        alertou = processar()

    assert alertou is True
    mock_enviar.assert_called_once()
    texto = mock_enviar.call_args.args[0]
    assert "motivo de teste" in texto


def test_problema_detectado_sem_secrets_configurados_nao_quebra(monkeypatch):
    monkeypatch.delenv("WATCHDOG_TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("WATCHDOG_TELEGRAM_CHAT_ID", raising=False)

    with patch("src.watchdog.fluxo.buscar_execucoes_recentes", return_value=[{}]), \
         patch("src.watchdog.fluxo.avaliar_execucoes", return_value=(True, "motivo de teste")), \
         patch("src.watchdog.fluxo.enviar_mensagem") as mock_enviar:
        alertou = processar()

    assert alertou is False
    mock_enviar.assert_not_called()
