"""
Orquestrador do fluxo de correção.

Esta classe é o único ponto que "conhece" a sequência completa do caso
de uso (carregar arquivos -> validar -> montar mensagem -> chamar LLM ->
validar resultado). Outros pontos de entrada (CLI, API web, testes)
devem depender só de AgenteCorrecao, e não remontar essa lógica.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from feedbackai.config import Settings
from ingestion.file_loader import ArquivoCarregado, carregar_par_avaliacao
from llm.client import criar_llm_estruturado
from prompts.systemprompt import PROMPT_CORRECAO
from schemas.avaliacao import AvaliacaoQuestao
from utils.validacao import (
    verificar_arquivos_distintos,
    verificar_resultado_avaliacao,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResultadoAvaliacao:
    """
    Envelope do resultado: separa a avaliação em si (o que vai para o
    aluno/professor) dos avisos internos de consistência (o que serve
    para quem opera o sistema perceber que o LLM fugiu de alguma regra).
    """

    avaliacao: AvaliacaoQuestao
    avisos: list[str]


class AgenteCorrecao:
    """
    O 'llm_estruturado' é recebido por injeção (com um default de
    conveniência) justamente para permitir testar a orquestração inteira
    com um cliente falso, sem depender de rede/API key (ver
    tests/test_agente_correcao.py).
    """

    def __init__(self, settings: Settings, llm_estruturado=None):
        self.settings = settings
        self.llm_estruturado = llm_estruturado or criar_llm_estruturado(settings)

    def avaliar(
        self,
        caminho_gabarito: str | Path,
        caminho_prova_aluno: str | Path,
    ) -> ResultadoAvaliacao:
        """
        Executa o fluxo completo de correção para um par (gabarito, prova).

        Levanta ArquivoNaoEncontradoError / ExtensaoNaoSuportadaError /
        ArquivoMuitoGrandeError / ArquivoIlegivelError (de file_loader) ou
        ArquivosInconsistentesError (de validacao) antes de qualquer
        chamada ao LLM — fail-fast, para não gastar uma chamada de API
        com uma entrada já sabidamente inválida.
        """
        gabarito, prova_aluno = carregar_par_avaliacao(
            caminho_gabarito, caminho_prova_aluno, self.settings
        )
        verificar_arquivos_distintos(gabarito, prova_aluno)

        mensagens = self._montar_mensagens(gabarito, prova_aluno)
        resposta = self.llm_estruturado.invoke(mensagens)
        if not isinstance(resposta, AvaliacaoQuestao):
            raise TypeError(
                f"Resposta inesperada do LLM: esperado AvaliacaoQuestao, recebido {type(resposta).__name__}"
            )
        avaliacao = resposta


        avisos = verificar_resultado_avaliacao(avaliacao)
        for aviso in avisos:
            logger.warning("Inconsistência na resposta do LLM: %s", aviso)

        return ResultadoAvaliacao(avaliacao=avaliacao, avisos=avisos)

    @staticmethod
    def _montar_mensagens(
        gabarito: ArquivoCarregado, prova_aluno: ArquivoCarregado
    ) -> list:
        """Monta a mensagem multimodal (system + human com os dois arquivos anexados)."""
        return [
            SystemMessage(content=PROMPT_CORRECAO),
            HumanMessage(
                content=[
                    {"type": "text", "text": "Arquivo do professor (gabarito):"},
                    gabarito.como_bloco_mensagem(),
                    {"type": "text", "text": "Arquivo do aluno (resposta):"},
                    prova_aluno.como_bloco_mensagem(),
                ]
            ),
        ]