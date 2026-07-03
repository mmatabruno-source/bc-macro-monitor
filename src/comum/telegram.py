"""Envio de mensagens ao Telegram, reaproveitado do padrão validado no copom-monitor-pm."""

import logging

from src.comum.http_retry import requisitar_com_retry

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"


class FalhaExternaTelegram(Exception):
    """Levantada quando o envio ao Telegram falha após todas as tentativas."""


def _sanitizar(texto, token):
    if not token:
        return texto
    return texto.replace(token, "***")


def _erro_de_formatacao(resposta):
    return resposta is not None and resposta.status_code == 400 and (
        "can't parse entities" in resposta.text.lower()
    )


def enviar_mensagem(texto, token, chat_id):
    """Envia uma mensagem ao Telegram, com fallback de Markdown para texto simples.

    Nunca perde uma notificação só por causa de formatação: se o Markdown for
    rejeitado, reenvia em texto simples antes de desistir.
    """
    url = f"{TELEGRAM_API_BASE}/bot{token}/sendMessage"

    try:
        resposta = requisitar_com_retry(
            "POST",
            url,
            json={"chat_id": chat_id, "text": texto, "parse_mode": "Markdown"},
        )
    except Exception as exc:
        raise FalhaExternaTelegram(_sanitizar(str(exc), token)) from exc

    if resposta is not None and resposta.ok:
        return resposta

    if _erro_de_formatacao(resposta):
        logger.warning("Markdown rejeitado pelo Telegram, reenviando em texto simples")
        try:
            resposta_texto_simples = requisitar_com_retry(
                "POST",
                url,
                json={"chat_id": chat_id, "text": texto},
            )
        except Exception as exc:
            raise FalhaExternaTelegram(_sanitizar(str(exc), token)) from exc

        if resposta_texto_simples is not None and resposta_texto_simples.ok:
            return resposta_texto_simples

        corpo = resposta_texto_simples.text if resposta_texto_simples is not None else "sem resposta"
        raise FalhaExternaTelegram(_sanitizar(corpo, token))

    corpo = resposta.text if resposta is not None else "sem resposta"
    raise FalhaExternaTelegram(_sanitizar(corpo, token))
