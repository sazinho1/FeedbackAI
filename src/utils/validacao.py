"""
Validações e regras de negócio que não devem depender só do que o
prompt "pede" ao LLM. Ela são "forçadas" em código para o caso do modelo não
seguir a instrução à risca.

Cobre principalmente a seção 7 do prompt original ("Casos de Erro") e a
regra de nota 100, que estavam descritas só em texto, sem nenhuma
checagem na programação correspondente.
"""

from __future__ import annotations

from ingestion.file_loader import ArquivoCarregado
from schemas.avaliacao import AvaliacaoQuestao


class ArquivosInconsistentesError(Exception):
    """Gabarito e prova do aluno parecem não corresponder à mesma avaliação."""


class ResultadoInconsistenteError(Exception):
    """A resposta estruturada do LLM viola uma regra de negócio conhecida."""


def verificar_arquivos_distintos(
    gabarito: ArquivoCarregado, prova_aluno: ArquivoCarregado
) -> None:
    """
    Checagem para ver o professor enviou o mesmo
    arquivo duas vezes (gabarito == prova do aluno). Isso pega um erro
    comum de upload antes de gastar uma chamada de API.
    """
    if gabarito.conteudo_base64 == prova_aluno.conteudo_base64:
        raise ArquivosInconsistentesError(
            "O arquivo do gabarito e o da prova do aluno são idênticos. "
            "Confirme se os arquivos corretos foram enviados."
        )


def verificar_resultado_avaliacao(resultado: AvaliacaoQuestao) -> list[str]:
    """
    Valida a resposta estruturada do LLM contra as regras de negócio do
    prompt original (seção 4: "Regras de Saída").

    Retorna uma lista de avisos (strings) em vez de levantar exceção
    diretamente para os casos "leves". A ideia é logar/expor esses
    avisos, não necessariamente interromper o fluxo, já que a causa é
    o modelo ter fugido da instrução, algo que acontece mesmo com
    schema forçado.

    Levanta ResultadoInconsistenteError apenas para inconsistências
    graves (nota fora do intervalo, por exemplo, que o `Field(ge=0, le=100)`
    do schema já deveria ter impedido, isto é, uma checagem redundante de propósito).
    """
    avisos: list[str] = []

    if not (0 <= resultado.nota <= 100):
        raise ResultadoInconsistenteError(
            f"Nota fora do intervalo esperado (0-100): {resultado.nota}"
        )

    if resultado.nota == 100:
        campos_que_deveriam_estar_vazios = {
            "itens": resultado.itens,
            "conteudos_para_rever": resultado.conteudos_para_rever,
            "fontes_sugeridas": resultado.fontes_sugeridas,
        }
        for nome_campo, valor in campos_que_deveriam_estar_vazios.items():
            if valor:
                avisos.append(
                    f"Nota 100 mas o campo '{nome_campo}' não está vazio "
                    "(esperado pela regra de saída simplificada)."
                )
    else:
        if not resultado.itens:
            avisos.append(
                "Nota diferente de 100, mas nenhum item foi detalhado em 'itens'."
            )
        if not resultado.conteudos_para_rever:
            avisos.append(
                "Nota diferente de 100, mas 'conteudos_para_rever' está vazio."
            )

    itens_incorretos_sem_explicacao = [
        item.questao
        for item in resultado.itens
        if item.status != "correto" and not item.explicacao_erro
    ]
    if itens_incorretos_sem_explicacao:
        avisos.append(
            "Itens marcados como incorretos/parciais sem 'explicacao_erro': "
            + ", ".join(itens_incorretos_sem_explicacao)
        )

    return avisos