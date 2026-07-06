from unittest.mock import MagicMock, patch

from src.relatorio.gerador_analise import MARCADOR_CIDADAO, MARCADOR_INVESTIDOR, _parse_resposta, gerar_analise


def test_parse_resposta_extrai_as_duas_secoes():
    texto = (
        f"{MARCADOR_CIDADAO}\n▪️ Tópico cidadão X.\n\n"
        f"{MARCADOR_INVESTIDOR}\n▪️ Tópico investidor Y."
    )

    analise = _parse_resposta(texto)

    assert analise.visao_cidadao == "▪️ Tópico cidadão X."
    assert analise.visao_investidor == "▪️ Tópico investidor Y."


@patch("src.relatorio.gerador_analise.anthropic.Anthropic")
@patch("src.relatorio.gerador_analise._baixar_pdf", return_value=b"conteudo-pdf-fake")
def test_gerar_analise_chama_claude_com_documento_pdf(mock_baixar, mock_anthropic_cls):
    texto_resposta = (
        f"{MARCADOR_CIDADAO}\n▪️ Cidadão.\n"
        f"{MARCADOR_INVESTIDOR}\n▪️ Investidor."
    )
    mock_cliente = MagicMock()
    mock_cliente.messages.create.return_value = MagicMock(
        content=[MagicMock(type="text", text=texto_resposta)]
    )
    mock_anthropic_cls.return_value = mock_cliente

    analise = gerar_analise("https://exemplo.com/relatorio.pdf")

    assert analise.visao_cidadao == "▪️ Cidadão."
    mock_baixar.assert_called_once_with("https://exemplo.com/relatorio.pdf")

    chamada = mock_cliente.messages.create.call_args
    conteudo = chamada.kwargs["messages"][0]["content"]
    assert conteudo[0]["type"] == "document"
    assert conteudo[0]["source"]["media_type"] == "application/pdf"


@patch("src.relatorio.gerador_analise.anthropic.Anthropic")
@patch("src.relatorio.gerador_analise._baixar_pdf", return_value=b"conteudo-pdf-fake")
def test_gerar_analise_ignora_thinking_block_antes_do_texto(mock_baixar, mock_anthropic_cls):
    """Reproduz o bug real de produção: com extended thinking, o content[0]
    da resposta é um ThinkingBlock (sem .text utilizável), e o texto de
    verdade vem num bloco 'text' posterior."""
    texto_resposta = (
        f"{MARCADOR_CIDADAO}\n▪️ Cidadão.\n"
        f"{MARCADOR_INVESTIDOR}\n▪️ Investidor."
    )
    mock_cliente = MagicMock()
    mock_cliente.messages.create.return_value = MagicMock(
        content=[
            MagicMock(type="thinking", text=None),
            MagicMock(type="text", text=texto_resposta),
        ]
    )
    mock_anthropic_cls.return_value = mock_cliente

    analise = gerar_analise("https://exemplo.com/relatorio.pdf")

    assert analise.visao_cidadao == "▪️ Cidadão."
