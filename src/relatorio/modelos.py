"""Entidades de dados do fluxo Relatório de Política Monetária (data-model.md)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RelatorioPoliticaMonetaria:
    identificador: str  # "YYYYMM"
    data_publicacao: str  # "YYYY-MM-DD"
    link_pdf: str
    link_pagina: str


@dataclass(frozen=True)
class AnaliseCritica:
    cenario_macro: str
    projecoes_inflacao: str
    implicacao_portfolio: str
