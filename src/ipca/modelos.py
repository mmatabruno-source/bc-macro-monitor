"""Entidades de dados do fluxo IPCA (data-model.md)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DivulgacaoIpca:
    mes_referencia: str  # "YYYY-MM"
    variacao_mensal: float


@dataclass(frozen=True)
class GrupoIpca:
    nome: str
    variacao_mensal: float
    peso_mensal: float
