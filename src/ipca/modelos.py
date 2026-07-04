"""Entidades de dados do fluxo IPCA (data-model.md)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DivulgacaoIpca:
    mes_referencia: str  # "YYYY-MM"
    variacao_mensal: float


@dataclass(frozen=True)
class LeituraImpactoIpca:
    direcao_vs_mes_anterior: str  # "acelerou" | "desacelerou" | "estavel"
    posicao_vs_meta: str  # "acima" | "abaixo" | "em_linha"
