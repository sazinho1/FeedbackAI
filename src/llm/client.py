"""
Factory de criação do cliente LLM.

Centraliza a montagem do ChatGoogleGenerativeAI + with_structured_output
num único lugar. Isso pra evitar repetir e divergir essa configuração em
outros pontos de entrada do projeto (CLI, API web, testes) e facilita
trocar modelo/provedor sem tocar na lógica de negócio em core/.
"""

from __future__ import annotations
from functools import lru_cache
from langchain_google_genai import ChatGoogleGenerativeAI

from feedbackai.config import Settings
from schemas.avaliacao import AvaliacaoQuestao


def criar_llm(settings: Settings) -> ChatGoogleGenerativeAI:
    """Cria o cliente base do Gemini, sem saída estruturada."""
    return ChatGoogleGenerativeAI(
        model=settings.model_name,
        google_api_key=settings.google_api_key,
        temperature=settings.temperature,
        max_retries=settings.max_retries,
        timeout=settings.timeout_segundos,
    )


def criar_llm_estruturado(settings: Settings):
    """
    Cria o cliente já configurado para forçar a saída no formato
    AvaliacaoQuestao (ver schemas/avaliacao.py).

    Retorna um Runnable cujo .invoke(...) devolve diretamente uma
    instância de AvaliacaoQuestao, não texto solto.
    """
    llm = criar_llm(settings)
    return llm.with_structured_output(AvaliacaoQuestao)


@lru_cache(maxsize=1)
def obter_llm_estruturado_padrao():
    """
    Versão com cache para uso simples (CLI/scripts): monta as
    configurações a partir do ambiente uma única vez por processo,
    em vez de recriar o cliente a cada chamada.

    Evitar em testes automatizados (o cache esconde a injeção de
    configurações diferentes) — lá, prefira chamar criar_llm_estruturado()
    diretamente com um Settings de teste.
    """
    from feedbackai.config import carregar_configuracoes

    settings = carregar_configuracoes()
    return criar_llm_estruturado(settings)