from unittest.mock import MagicMock, patch

from src.relatorio.gerador_analise import MARCADOR_CENARIO, MARCADOR_PORTFOLIO, MARCADOR_PROJECOES, _parse_resposta, gerar_analise


def test_parse_resposta_extrai_as_tres_secoes():
    texto = (
        f"{MARCADOR_CENARIO}\nO cenário está X.\n\n"
        f"{MARCADOR_PROJECOES}\nAs projeções indicam Y.\n\n"
        f"{MARCADOR_PORTFOLIO}\nPara portfólio, isso significa Z."
    )

    analise = _parse_resposta(texto)

    assert analise.cenario_macro == "O cenário está X."
    assert analise.projecoes_inflacao == "As projeções indicam Y."
    assert analise.implicacao_portfolio == "Para portfólio, isso significa Z."


@patch("src.relatorio.gerador_analise.anthropic.Anthropic")
@patch("src.relatorio.gerador_analise._baixar_pdf", return_value=b"conteudo-pdf-fake")
def test_gerar_analise_chama_claude_com_documento_pdf(mock_baixar, mock_anthropic_cls):
    texto_resposta = (
        f"{MARCADOR_CENARIO}\nCenário.\n"
        f"{MARCADOR_PROJECOES}\nProjeções.\n"
        f"{MARCADOR_PORTFOLIO}\nPortfólio."
    )
    mock_cliente = MagicMock()
    mock_cliente.messages.create.return_value = MagicMock(
        content=[MagicMock(text=texto_resposta)]
    )
    mock_anthropic_cls.return_value = mock_cliente

    analise = gerar_analise("https://exemplo.com/relatorio.pdf")

    assert analise.cenario_macro == "Cenário."
    mock_baixar.assert_called_once_with("https://exemplo.com/relatorio.pdf")

    chamada = mock_cliente.messages.create.call_args
    conteudo = chamada.kwargs["messages"][0]["content"]
    assert conteudo[0]["type"] == "document"
    assert conteudo[0]["source"]["media_type"] == "application/pdf"
