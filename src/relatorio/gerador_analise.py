"""Geração da análise crítica a partir do PDF do relatório, via Claude API
(suporte nativo a documento PDF — sem biblioteca de extração de texto,
ver specs/002-relatorio-politica-monetaria/research.md, R3)."""

import base64
import os

import anthropic

from src.comum.http_retry import requisitar_com_retry
from src.relatorio.modelos import AnaliseCritica

MODELO = "claude-sonnet-5"
MAX_TOKENS = 2048

MARCADOR_CENARIO = "### CENARIO_MACRO"
MARCADOR_PROJECOES = "### PROJECOES_INFLACAO"
MARCADOR_PORTFOLIO = "### IMPLICACAO_PORTFOLIO"

PROMPT = f"""\
Você é um analista de portfólio lendo o Relatório de Política Monetária
anexado (PDF) do Banco Central do Brasil. Responda em português, em texto
corrido (sem markdown), organizado EXATAMENTE nas 3 seções abaixo, cada uma
iniciada por seu marcador em uma linha própria:

{MARCADOR_CENARIO}
<parágrafo curto sobre o cenário macroeconômico descrito no relatório>

{MARCADOR_PROJECOES}
<parágrafo curto sobre as projeções oficiais de inflação>

{MARCADOR_PORTFOLIO}
<parágrafo curto com a leitura de implicação para decisões de portfólio>
"""


def _baixar_pdf(url):
    resposta = requisitar_com_retry("GET", url)
    resposta.raise_for_status()
    return resposta.content


def _extrair_secao(texto, marcador, proximo_marcador=None):
    inicio = texto.index(marcador) + len(marcador)
    fim = texto.index(proximo_marcador, inicio) if proximo_marcador else len(texto)
    return texto[inicio:fim].strip()


def _parse_resposta(texto):
    return AnaliseCritica(
        cenario_macro=_extrair_secao(texto, MARCADOR_CENARIO, MARCADOR_PROJECOES),
        projecoes_inflacao=_extrair_secao(texto, MARCADOR_PROJECOES, MARCADOR_PORTFOLIO),
        implicacao_portfolio=_extrair_secao(texto, MARCADOR_PORTFOLIO),
    )


def gerar_analise(link_pdf):
    """Baixa o PDF e envia como documento nativo à Claude API, retornando
    uma AnaliseCritica. Levanta exceção se a chamada ou o parsing falhar
    (tratado como falha isolada pelo chamador, com fallback FR-006)."""
    pdf_bytes = _baixar_pdf(link_pdf)
    pdf_base64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

    cliente = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    resposta = cliente.messages.create(
        model=MODELO,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_base64,
                        },
                    },
                    {"type": "text", "text": PROMPT},
                ],
            }
        ],
    )

    texto = resposta.content[0].text
    return _parse_resposta(texto)
