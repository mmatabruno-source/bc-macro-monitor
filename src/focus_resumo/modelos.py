"""Entidades de dados do fluxo Resumo Semanal do Focus (data-model.md)."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValorIndicadorAno:
    indicador: str
    ano: str
    valor: float


@dataclass(frozen=True)
class DivulgacaoFocusResumo:
    data_referencia: str
    valores: list = field(default_factory=list)
