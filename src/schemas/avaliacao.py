"""
Schema de saída estruturada do FeedbackAÍ. Ele (e não o texto do
prompt) que o `with_structured_output` obriga o modelo a seguir.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class ItemAvaliado(BaseModel):
    """Avaliação de uma questão/item específico da prova."""

    questao: str = Field(description="Identificação da questão (ex: 'Questão 1, item a')")
    status: Literal["correto", "parcialmente_correto", "incorreto"]
    resposta_aluno: str = Field(description="Resumo da resposta dada pelo aluno")
    resposta_esperada: str = Field(description="Resumo da resposta/resolução esperada pelo professor")
    explicacao_erro: Optional[str] = Field(
        default=None, description="O que está errado ou incompleto (None se status = correto)"
    )
    correcao_detalhada: Optional[str] = Field(
        default=None, description="Resolução correta passo a passo (None se status = correto)"
    )


class FonteSugerida(BaseModel):
    """Material de estudo sugerido para um conteúdo a revisar."""

    topico: str = Field(description="Conceito relacionado")
    sugestao: str = Field(
        description="Tipo de material recomendado (livro, capítulo, vídeo, documentação oficial); "
        "nunca um título/link inventado"
    )


class AvaliacaoQuestao(BaseModel):
    """Resultado completo da correção de uma prova."""

    nota: int = Field(ge=0, le=100, description="Nota final da prova, de 0 a 100")
    resumo_geral: str = Field(description="Resumo do desempenho do aluno em até 3 frases")
    itens: list[ItemAvaliado] = Field(
        default_factory=list, description="Avaliação item a item da prova"
    )
    conteudos_para_rever: list[str] = Field(
        default_factory=list,
        description="Conteúdos necessários para resolver corretamente os itens errados/parciais",
    )
    fontes_sugeridas: list[FonteSugerida] = Field(
        default_factory=list, description="Materiais de estudo sugeridos para os conteúdos a revisar"
    )

