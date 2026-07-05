"""Script TEMPORÁRIO de verificação manual: envia, com dados reais, uma
mensagem de cada um dos dois fluxos do Focus — (1) Focus/Copom
(expectativa de Selic para a próxima reunião) e (2) Resumo Semanal do
Focus (última divulgação comparada à penúltima) — para conferência
visual do formato. Não lê nem grava estado.json (só leitura da API +
envio), sem efeito colateral na produção. Remover após o uso."""

import os

from src.comum.http_retry import requisitar_com_retry
from src.comum.telegram import enviar_mensagem
from src.focus.cliente_expectativas import buscar_proxima_reuniao
from src.focus.cliente_selic_atual import buscar_selic_vigente
from src.focus.fluxo import _montar_mensagem as montar_mensagem_copom
from src.focus_resumo.cliente_expectativas_anuais import INDICADORES, _anos_padrao, _montar_url, _parse_valores
from src.focus_resumo.comparador import comparar_valores
from src.focus_resumo.fluxo import _montar_mensagem as montar_mensagem_resumo
from src.focus_resumo.modelos import DivulgacaoFocusResumo


def _duas_datas_mais_recentes():
    url = _montar_url({
        "$filter": "Indicador eq 'IPCA'",
        "$orderby": "Data desc",
        "$top": "100",
        "$format": "json",
    })
    resposta = requisitar_com_retry("GET", url)
    resposta.raise_for_status()
    linhas = resposta.json()["value"]
    datas = []
    for linha in linhas:
        if linha["Data"] not in datas:
            datas.append(linha["Data"])
        if len(datas) == 2:
            break
    return datas


def _buscar_divulgacao_resumo(data_referencia, anos):
    filtro_indicadores = " or ".join(f"Indicador eq '{ind}'" for ind in INDICADORES)
    url = _montar_url({
        "$filter": f"Data eq '{data_referencia}' and ({filtro_indicadores})",
        "$format": "json",
    })
    resposta = requisitar_com_retry("GET", url)
    resposta.raise_for_status()
    linhas = resposta.json()["value"]
    return DivulgacaoFocusResumo(data_referencia=data_referencia, valores=_parse_valores(linhas, anos))


def _mensagem_focus_copom():
    atual = buscar_proxima_reuniao()
    selic_vigente = buscar_selic_vigente()
    return montar_mensagem_copom(atual, selic_vigente)


def _mensagem_focus_resumo():
    datas = _duas_datas_mais_recentes()
    print("Datas encontradas:", datas)
    if len(datas) < 2:
        print("Não há 2 divulgações distintas disponíveis — abortando essa mensagem.")
        return None

    data_ultima, data_penultima = datas[0], datas[1]
    anos = _anos_padrao()

    divulgacao_penultima = _buscar_divulgacao_resumo(data_penultima, anos)
    divulgacao_ultima = _buscar_divulgacao_resumo(data_ultima, anos)

    valores_penultima_dict = {f"{i.indicador}:{i.ano}": i.valor for i in divulgacao_penultima.valores}
    direcoes_ultima = comparar_valores(valores_penultima_dict, divulgacao_ultima.valores)
    return montar_mensagem_resumo(divulgacao_ultima, direcoes_ultima, valores_penultima_dict)


def main():
    token = os.environ["FOCUS_TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["FOCUS_TELEGRAM_CHAT_ID"]

    mensagem_copom = _mensagem_focus_copom()
    print("=== MENSAGEM 1 (Focus/Copom) ===")
    print(mensagem_copom)
    enviar_mensagem(mensagem_copom, token, chat_id)

    mensagem_resumo = _mensagem_focus_resumo()
    if mensagem_resumo is not None:
        print("=== MENSAGEM 2 (Resumo Semanal do Focus) ===")
        print(mensagem_resumo)
        enviar_mensagem(mensagem_resumo, token, chat_id)


if __name__ == "__main__":
    main()
