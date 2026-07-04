"""Script manual único para diagnosticar se as falhas de conexão são causadas
por rota IPv6 quebrada (hipótese: DNS resolve AAAA, mas a rota IPv6 real está
bloqueada/sem resposta, causando ConnectTimeout onde IPv4 funcionaria).
Remover após o teste."""

import socket
import time

import requests
import urllib3.util.connection as urllib3_cn

HOSTS = [
    ("apisidra.ibge.gov.br", 443),
    ("servicodados.ibge.gov.br", 443),
    ("www.ipeadata.gov.br", 80),
]


def resolver(host, porta):
    try:
        enderecos = socket.getaddrinfo(host, porta)
        familias = sorted({info[0].name for info in enderecos})
        ips = sorted({info[4][0] for info in enderecos})
        return familias, ips
    except Exception as exc:
        return None, str(exc)


def testar_conexao_raw(host, porta, family, timeout=8):
    inicio = time.monotonic()
    try:
        enderecos = socket.getaddrinfo(host, porta, family)
        ip = enderecos[0][4][0]
        with socket.socket(family, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((ip, porta))
        return True, ip, time.monotonic() - inicio
    except Exception as exc:
        return False, str(exc), time.monotonic() - inicio


def main():
    for host, porta in HOSTS:
        print(f"\n=== {host}:{porta} ===")
        familias, ips = resolver(host, porta)
        print(f"DNS: familias={familias} ips={ips}")

        ok4, info4, dur4 = testar_conexao_raw(host, porta, socket.AF_INET)
        print(f"IPv4 direto: ok={ok4} info={info4} duracao={dur4:.2f}s")

        ok6, info6, dur6 = testar_conexao_raw(host, porta, socket.AF_INET6)
        print(f"IPv6 direto: ok={ok6} info={info6} duracao={dur6:.2f}s")

    print("\n=== Teste HTTP real forçando IPv4 (monkeypatch urllib3) ===")
    urllib3_cn.allowed_gai_family = lambda: socket.AF_INET
    url = (
        "https://servicodados.ibge.gov.br/api/v3/agregados/7060/periodos/-1/"
        "variaveis/63|66?localidades=N1[all]&classificacao=315[7169,7170]"
    )
    try:
        resposta = requests.get(url, timeout=15)
        print(f"status_code={resposta.status_code} (forçando IPv4)")
    except Exception as exc:
        print(f"FALHOU mesmo forçando IPv4: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
