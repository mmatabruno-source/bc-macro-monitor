from unittest.mock import patch

from src.comum.isolamento import _executar_isolado, notificar_falha
from src.comum.telegram import FalhaExternaTelegram


def test_excecao_nao_se_propaga():
    def fluxo_com_erro():
        raise ValueError("falha simulada")

    resultado = _executar_isolado("fluxo-fake", fluxo_com_erro)

    assert resultado["falhou"] is True
    assert resultado["processado"] is False
    assert isinstance(resultado["erro"], ValueError)


def test_fluxo_sem_erro_retorna_processado():
    resultado = _executar_isolado("fluxo-fake", lambda: True)

    assert resultado["falhou"] is False
    assert resultado["processado"] is True


@patch("src.comum.isolamento.logger")
def test_excecao_e_logada(mock_logger):
    def fluxo_com_erro():
        raise RuntimeError("boom")

    _executar_isolado("fluxo-fake", fluxo_com_erro)

    mock_logger.error.assert_called_once()


@patch("src.comum.isolamento.enviar_mensagem")
def test_notificar_falha_envia_para_o_bot_correto(mock_enviar):
    notificar_falha("Fluxo Fake", RuntimeError("boom"), token="token-fake", chat_id="chat-fake")

    mock_enviar.assert_called_once()
    args, kwargs = mock_enviar.call_args
    assert "Fluxo Fake" in args[0]
    assert "boom" in args[0]
    assert kwargs["token"] == "token-fake"
    assert kwargs["chat_id"] == "chat-fake"


@patch("src.comum.isolamento.enviar_mensagem", side_effect=FalhaExternaTelegram("Telegram fora do ar"))
def test_notificar_falha_nao_propaga_se_telegram_tambem_falhar(mock_enviar):
    # Não deve levantar exceção mesmo se o próprio alerta de falha não puder ser entregue.
    notificar_falha("Fluxo Fake", RuntimeError("boom"), token="token-fake", chat_id="chat-fake")

    mock_enviar.assert_called_once()
