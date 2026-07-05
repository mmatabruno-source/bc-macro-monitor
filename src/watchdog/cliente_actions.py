"""Cliente HTTP da API de execuções do GitHub Actions, para o watchdog
consultar o histórico do workflow de produção (monitor.yml)."""

from src.comum.http_retry import requisitar_com_retry

BASE_URL = "https://api.github.com"


def buscar_execucoes_recentes(owner, repo, workflow_arquivo, token, por_pagina=10):
    """Retorna a lista de execuções recentes de `workflow_arquivo`
    (ex.: "monitor.yml"), da mais recente para a mais antiga — mesmo
    formato usado por `verificar.avaliar_execucoes`."""
    url = f"{BASE_URL}/repos/{owner}/{repo}/actions/workflows/{workflow_arquivo}/runs"
    resposta = requisitar_com_retry(
        "GET",
        url,
        params={"per_page": por_pagina},
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
    )
    resposta.raise_for_status()
    return resposta.json()["workflow_runs"]
