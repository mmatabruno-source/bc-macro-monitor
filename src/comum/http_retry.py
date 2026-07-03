"""Retry HTTP seletivo, reaproveitado do padrão validado no copom-monitor-pm."""

import logging
import re
import time

import requests

logger = logging.getLogger(__name__)

ESPERA_INICIAL_SEGUNDOS = 2
MAX_TENTATIVAS_PADRAO = 3

_PADRAO_TOKEN_TELEGRAM = re.compile(r"/bot[^/]+/")


def _url_sanitizada(url):
    # URLs do Telegram carregam o token do bot no path (/bot<token>/...);
    # nunca logar isso em texto plano (Princípio IX).
    return _PADRAO_TOKEN_TELEGRAM.sub("/bot***/", url)


def _retentavel(status_code):
    # 429 (limite de taxa) e 5xx (indisponibilidade momentânea) são tipicamente
    # transitórios; qualquer outro 4xx (ex.: 404) é permanente — insistir não ajuda.
    return status_code == 429 or status_code >= 500


def _espera_para_tentativa(resposta, tentativa):
    if resposta is not None and resposta.status_code == 429:
        retry_after = resposta.headers.get("Retry-After")
        if retry_after is not None:
            try:
                return float(retry_after)
            except ValueError:
                pass
    return ESPERA_INICIAL_SEGUNDOS * tentativa


def requisitar_com_retry(metodo, url, max_tentativas=MAX_TENTATIVAS_PADRAO, **kwargs):
    """Executa uma requisição HTTP com retry seletivo em 429/5xx.

    Levanta a última exceção/resposta se todas as tentativas falharem.
    """
    resposta = None
    for tentativa in range(1, max_tentativas + 1):
        try:
            resposta = requests.request(metodo, url, **kwargs)
        except requests.RequestException as exc:
            if tentativa == max_tentativas:
                raise
            logger.warning(
                "Falha de rede na tentativa %d/%d para %s: %s",
                tentativa,
                max_tentativas,
                _url_sanitizada(url),
                exc,
            )
            time.sleep(_espera_para_tentativa(None, tentativa))
            continue

        if not _retentavel(resposta.status_code):
            return resposta

        if tentativa == max_tentativas:
            return resposta

        logger.warning(
            "Resposta %d na tentativa %d/%d para %s — retentando",
            resposta.status_code,
            tentativa,
            max_tentativas,
            _url_sanitizada(url),
        )
        time.sleep(_espera_para_tentativa(resposta, tentativa))

    return resposta
