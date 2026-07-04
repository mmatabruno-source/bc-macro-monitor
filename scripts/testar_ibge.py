"""Última tentativa: buscar o $metadata do serviço para confirmar nomes reais
de entidades/campos, e testar sem $filter algum (só listar). Remover após o
teste."""

import requests

BASE = "http://www.ipeadata.gov.br/api/odata4"


def main():
    print("=== $metadata (schema real) ===")
    try:
        resposta = requests.get(f"{BASE}/$metadata", timeout=15)
        print(f"status_code={resposta.status_code}")
        print(resposta.text[:3000])
    except Exception as exc:
        print(f"FALHOU: {type(exc).__name__}: {exc}")

    print("\n=== Metadados sem nenhum parametro ===")
    try:
        resposta = requests.get(f"{BASE}/Metadados", timeout=15)
        print(f"status_code={resposta.status_code}")
        print(resposta.text[:1500])
    except Exception as exc:
        print(f"FALHOU: {type(exc).__name__}: {exc}")

    print("\n=== Metadados com $top apenas ===")
    try:
        resposta = requests.get(f"{BASE}/Metadados", params={"$top": 3}, timeout=15)
        print(f"url final: {resposta.url}")
        print(f"status_code={resposta.status_code}")
        print(resposta.text[:1500])
    except Exception as exc:
        print(f"FALHOU: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
