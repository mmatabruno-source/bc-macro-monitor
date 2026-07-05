from unittest.mock import MagicMock, patch

import pytest

from src.comum.telegram import FalhaExternaTelegram, _sanitizar, enviar_mensagem


def _resposta(ok, status_code=200, text=""):
    resposta = MagicMock()
    resposta.ok = ok
    resposta.status_code = status_code
    resposta.text = text
    return resposta


def test_sanitizar_remove_token():
    texto = "erro ao chamar https://api.telegram.org/bot123:ABC/sendMessage"

    assert _sanitizar(texto, "123:ABC") == "erro ao chamar https://api.telegram.org/bot***/sendMessage"


def test_sanitizar_sem_token_retorna_texto_original():
    assert _sanitizar("texto qualquer", None) == "texto qualquer"


@patch("src.comum.telegram.requisitar_com_retry")
def test_envio_com_sucesso_nao_precisa_de_fallback(mock_requisitar):
    mock_requisitar.return_value = _resposta(ok=True)

    resposta = enviar_mensagem("*texto*", "token-fake", "chat-fake")

    assert resposta.ok is True
    mock_requisitar.assert_called_once()
    assert mock_requisitar.call_args.kwargs["json"]["parse_mode"] == "Markdown"


@patch("src.comum.telegram.requisitar_com_retry")
def test_markdown_rejeitado_reenvia_em_texto_simples(mock_requisitar):
    resposta_markdown_rejeitado = _resposta(
        ok=False, status_code=400, text="Bad Request: can't parse entities: some error"
    )
    resposta_texto_simples_ok = _resposta(ok=True)
    mock_requisitar.side_effect = [resposta_markdown_rejeitado, resposta_texto_simples_ok]

    resposta = enviar_mensagem("*texto*", "token-fake", "chat-fake")

    assert resposta.ok is True
    assert mock_requisitar.call_count == 2
    segunda_chamada = mock_requisitar.call_args_list[1]
    assert "parse_mode" not in segunda_chamada.kwargs["json"]


@patch("src.comum.telegram.requisitar_com_retry")
def test_markdown_rejeitado_e_fallback_tambem_falha_levanta_excecao(mock_requisitar):
    resposta_markdown_rejeitado = _resposta(
        ok=False, status_code=400, text="Bad Request: can't parse entities: some error"
    )
    resposta_texto_simples_falha = _resposta(ok=False, status_code=500, text="erro interno")
    mock_requisitar.side_effect = [resposta_markdown_rejeitado, resposta_texto_simples_falha]

    with pytest.raises(FalhaExternaTelegram):
        enviar_mensagem("*texto*", "token-fake", "chat-fake")


@patch("src.comum.telegram.requisitar_com_retry")
def test_erro_nao_relacionado_a_formatacao_levanta_excecao_sem_tentar_fallback(mock_requisitar):
    mock_requisitar.return_value = _resposta(ok=False, status_code=403, text="Forbidden")

    with pytest.raises(FalhaExternaTelegram):
        enviar_mensagem("texto", "token-fake", "chat-fake")

    mock_requisitar.assert_called_once()


@patch("src.comum.telegram.requisitar_com_retry", side_effect=RuntimeError("falha de rede"))
def test_falha_de_rede_levanta_falha_externa_com_token_sanitizado(mock_requisitar):
    with pytest.raises(FalhaExternaTelegram) as exc_info:
        enviar_mensagem("texto", "token-secreto", "chat-fake")

    assert "token-secreto" not in str(exc_info.value)
