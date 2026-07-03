from unittest.mock import patch

from src.comum.isolamento import _executar_isolado


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
