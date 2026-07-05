"""Lógica pura de decisão do watchdog: dado o histórico recente de
execuções do workflow de produção (monitor.yml), decide se deve alertar.

Sem I/O — só recebe dados já buscados, pra ser fácil de testar."""

from datetime import datetime, timedelta, timezone

LIMITE_HORAS_PADRAO = 30
FALHAS_CONSECUTIVAS_PADRAO = 3


def _parse_data(texto):
    return datetime.fromisoformat(texto.replace("Z", "+00:00"))


def avaliar_execucoes(
    execucoes,
    agora=None,
    limite_horas=LIMITE_HORAS_PADRAO,
    falhas_consecutivas_para_alerta=FALHAS_CONSECUTIVAS_PADRAO,
):
    """`execucoes`: lista de dicts com pelo menos "conclusion" e "created_at"
    (formato da API de execuções do GitHub Actions), ordenada da mais
    recente para a mais antiga.

    Retorna (deve_alertar: bool, motivo: str | None).

    Nunca alerta se a lista estiver vazia (cold start de um workflow
    recém-criado, ou primeira checagem antes de qualquer execução)."""
    if not execucoes:
        return False, None

    agora = agora or datetime.now(timezone.utc)
    mais_recente = execucoes[0]
    idade = agora - _parse_data(mais_recente["created_at"])
    if idade > timedelta(hours=limite_horas):
        return True, (
            f"nenhuma execução de monitor.yml nas últimas {limite_horas}h "
            f"(última em {mais_recente['created_at']})"
        )

    ultimas = execucoes[:falhas_consecutivas_para_alerta]
    if len(ultimas) == falhas_consecutivas_para_alerta and all(
        e.get("conclusion") == "failure" for e in ultimas
    ):
        return True, f"as últimas {falhas_consecutivas_para_alerta} execuções de monitor.yml falharam"

    return False, None
