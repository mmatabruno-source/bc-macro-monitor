"""Leitura/escrita de estado.json por chave de fluxo, sem depender do formato interno de nenhum fluxo específico."""

import json
from pathlib import Path

ESTADO_PATH = Path(__file__).resolve().parent.parent.parent / "estado.json"


def ler_estado(chave, caminho=ESTADO_PATH):
    """Retorna o valor registrado para `chave`, ou None se ausente."""
    if not caminho.exists():
        return None
    with open(caminho, "r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    return dados.get(chave)


def gravar_estado(chave, valor, caminho=ESTADO_PATH):
    """Grava `valor` sob `chave`, preservando as demais chaves já existentes."""
    dados = {}
    if caminho.exists():
        with open(caminho, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

    dados[chave] = valor

    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2, sort_keys=True)
        arquivo.write("\n")
