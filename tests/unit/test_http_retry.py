from unittest.mock import patch

from src.comum.http_retry import (
    _espera_para_tentativa,
    _retentavel,
    _url_sanitizada,
    requisitar_com_retry,
)


class RespostaFake:
    def __init__(self, status_code, headers=None, text=""):
        self.status_code = status_code
        self.headers = headers or {}
        self.text = text


def test_retentavel_em_429():
    assert _retentavel(429) is True


def test_retentavel_em_5xx():
    assert _retentavel(500) is True
    assert _retentavel(503) is True


def test_nao_retentavel_em_404():
    assert _retentavel(404) is False


def test_nao_retentavel_em_200():
    assert _retentavel(200) is False


def test_espera_respeita_retry_after():
    resposta = RespostaFake(429, headers={"Retry-After": "10"})
    assert _espera_para_tentativa(resposta, 1) == 10.0


def test_espera_ignora_retry_after_invalido():
    resposta = RespostaFake(429, headers={"Retry-After": "abc"})
    assert _espera_para_tentativa(resposta, 2) == 4.0


def test_espera_exponencial_sem_retry_after():
    resposta = RespostaFake(500)
    assert _espera_para_tentativa(resposta, 1) == 2.0
    assert _espera_para_tentativa(resposta, 2) == 4.0


@patch("src.comum.http_retry.time.sleep", return_value=None)
@patch("src.comum.http_retry.requests.request")
def test_requisitar_com_retry_retenta_e_retorna_sucesso(mock_request, _mock_sleep):
    mock_request.side_effect = [RespostaFake(503), RespostaFake(200, text="ok")]

    resposta = requisitar_com_retry("GET", "https://exemplo.com", max_tentativas=3)

    assert resposta.status_code == 200
    assert mock_request.call_count == 2


@patch("src.comum.http_retry.time.sleep", return_value=None)
@patch("src.comum.http_retry.requests.request")
def test_requisitar_com_retry_nao_retenta_404(mock_request, _mock_sleep):
    mock_request.return_value = RespostaFake(404)

    resposta = requisitar_com_retry("GET", "https://exemplo.com", max_tentativas=3)

    assert resposta.status_code == 404
    assert mock_request.call_count == 1


def test_url_sanitizada_remove_token_telegram():
    url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

    assert _url_sanitizada(url) == "https://api.telegram.org/bot***/sendMessage"


@patch("src.comum.http_retry.time.sleep", return_value=None)
@patch("src.comum.http_retry.requests.request")
def test_retry_nao_vaza_token_no_log(mock_request, _mock_sleep, caplog):
    mock_request.side_effect = [RespostaFake(503), RespostaFake(200, text="ok")]
    url = "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"

    with caplog.at_level("WARNING"):
        requisitar_com_retry("POST", url, max_tentativas=3)

    assert "123456:ABC-DEF" not in caplog.text
    assert "bot***" in caplog.text
