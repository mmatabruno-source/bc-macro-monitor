import json

from src.comum.estado import gravar_estado, ler_estado


def test_ler_estado_chave_ausente_retorna_none(tmp_path):
    caminho = tmp_path / "estado.json"
    caminho.write_text("{}")

    assert ler_estado("nao_existe", caminho=caminho) is None


def test_ler_estado_arquivo_ausente_retorna_none(tmp_path):
    caminho = tmp_path / "nao_criado.json"

    assert ler_estado("qualquer", caminho=caminho) is None


def test_gravar_e_ler_estado(tmp_path):
    caminho = tmp_path / "estado.json"
    caminho.write_text("{}")

    gravar_estado("chave_a", {"valor": 1}, caminho=caminho)

    assert ler_estado("chave_a", caminho=caminho) == {"valor": 1}


def test_gravar_estado_preserva_outras_chaves(tmp_path):
    caminho = tmp_path / "estado.json"
    caminho.write_text(json.dumps({"chave_existente": "mantido"}))

    gravar_estado("chave_nova", "novo_valor", caminho=caminho)

    dados = json.loads(caminho.read_text())
    assert dados["chave_existente"] == "mantido"
    assert dados["chave_nova"] == "novo_valor"
