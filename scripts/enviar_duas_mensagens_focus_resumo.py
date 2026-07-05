"""Script TEMPORÁRIO de verificação manual: busca as duas últimas
divulgações reais do Resumo Semanal do Focus (penúltima e última) e envia
as duas mensagens reais no Telegram, comparando a última contra a
penúltima — para conferência visual do formato. Não lê nem grava
estado.json (só leitura da API + envio), sem efeito colateral na
produção. Remover após o uso."""

import os

from src.comum.http_retry import requisitar_com_retry
from src.comum.telegram import enviar_mensagem
from src.focus_resumo.cliente_expectativas_anuais import INDICADORES, _anos_padrao, _montar_url, _parse_valores
from src.focus_resumo.comparador import comparar_valores
from src.focus_resumo.fluxo import _montar_mensagem
from src.focus_resumo.modelos import DivulgacaoFocusResumo


def _duas_datas_mais_recentes():
    url = _montar_url({
        "$filter": "Indicador eq 'IPCA'",
        "$orderby": "Data desc",
        "$top": "10",
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


def _buscar_divulgacao(data_referencia, anos):
    filtro_indicadores = " or ".join(f"Indicador eq '{ind}'" for ind in INDICADORES)
    url = _montar_url({
        "$filter": f"Data eq '{data_referencia}' and ({filtro_indicadores})",
        "$format": "json",
    })
    resposta = requisitar_com_retry("GET", url)
    resposta.raise_for_status()
    linhas = resposta.json()["value"]
    return DivulgacaoFocusResumo(data_referencia=data_referencia, valores=_parse_valores(linhas, anos))


def main():
    datas = _duas_datas_mais_recentes()
    print("Datas encontradas:", datas)
    if len(datas) < 2:
        print("Não há 2 divulgações distintas disponíveis — abortando.")
        return

    data_ultima, data_penultima = datas[0], datas[1]
    anos = _anos_padrao()

    divulgacao_penultima = _buscar_divulgacao(data_penultima, anos)
    divulgacao_ultima = _buscar_divulgacao(data_ultima, anos)

    valores_penultima_dict = {f"{i.indicador}:{i.ano}": i.valor for i in divulgacao_penultima.valores}
    mensagem_penultima = _montar_mensagem(divulgacao_penultima, comparar_valores({}, divulgacao_penultima.valores), {})

    direcoes_ultima = comparar_valores(valores_penultima_dict, divulgacao_ultima.valores)
    mensagem_ultima = _montar_mensagem(divulgacao_ultima, direcoes_ultima, valores_penultima_dict)

    print("=== MENSAGEM 1 (penúltima:", data_penultima, ") ===")
    print(mensagem_penultima)
    print("=== MENSAGEM 2 (última:", data_ultima, ", comparada à penúltima) ===")
    print(mensagem_ultima)

    token = os.environ["FOCUS_TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["FOCUS_TELEGRAM_CHAT_ID"]
    enviar_mensagem(mensagem_penultima, token, chat_id)
    enviar_mensagem(mensagem_ultima, token, chat_id)


if __name__ == "__main__":
    main()
