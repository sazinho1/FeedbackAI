"""
Ingestão de arquivos (gabarito e prova do aluno) para envio multimodal ao LLM.

Este módulo resolve o ponto que faltava no script original: o código
descrevia um agente que recebe .txt/.pdf/.png, mas nunca lia nem
anexava nenhum arquivo de fato à chamada do modelo. Isolar essa lógica
aqui também facilita testar com mocks, sem precisar de uma API key real.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

from ai.config import MIME_TYPES_SUPORTADOS, Settings


class ArquivoNaoEncontradoError(Exception):
    """O caminho informado não existe ou não é um arquivo."""


class ExtensaoNaoSuportadaError(Exception):
    """A extensão do arquivo não está entre as suportadas pelo pipeline."""


class ArquivoMuitoGrandeError(Exception):
    """O arquivo excede o limite de tamanho configurado."""


class ArquivoIlegivelError(Exception):
    """O arquivo existe mas não pôde ser lido (permissão, corrompido, etc.)."""


@dataclass(frozen=True)
class ArquivoCarregado:
    """Representa um arquivo já lido e pronto para virar bloco de mensagem multimodal."""

    caminho: Path
    mime_type: str
    conteudo_base64: str

    def como_bloco_mensagem(self) -> dict:
        """
        Converte para o formato de bloco de conteúdo multimodal aceito pelo
        LangChain (HumanMessage com content em lista de blocos).

        Mantido como método separado porque o formato exato do bloco pode
        mudar entre versões do langchain-google-genai — se isso acontecer,
        só este método precisa ser ajustado, não quem o chama.
        """
        return {
            "type": "media",
            "mime_type": self.mime_type,
            "data": self.conteudo_base64,
        }


def _validar_arquivo(caminho: Path, settings: Settings) -> str:
    """Roda as checagens de existência/extensão/tamanho e retorna o mime type."""
    if not caminho.is_file():
        raise ArquivoNaoEncontradoError(f"Arquivo não encontrado: {caminho}")

    extensao = caminho.suffix.lower()
    if extensao not in settings.extensoes_suportadas:
        suportadas = ", ".join(settings.extensoes_suportadas)
        raise ExtensaoNaoSuportadaError(
            f"Extensão '{extensao}' não suportada para '{caminho.name}'. "
            f"Extensões aceitas: {suportadas}"
        )

    tamanho = caminho.stat().st_size
    if tamanho > settings.tamanho_max_arquivo_bytes:
        raise ArquivoMuitoGrandeError(
            f"'{caminho.name}' tem {tamanho / (1024 * 1024):.1f}MB, "
            f"acima do limite de {settings.tamanho_max_arquivo_mb}MB."
        )

    return MIME_TYPES_SUPORTADOS[extensao]


def carregar_arquivo(caminho: str | Path, settings: Settings) -> ArquivoCarregado:
    """
    Lê um arquivo do disco, valida e retorna um ArquivoCarregado pronto
    pra ser anexado a uma mensagem multimodal.
    """
    caminho = Path(caminho)
    mime_type = _validar_arquivo(caminho, settings)

    try:
        conteudo_bruto = caminho.read_bytes()
    except OSError as exc:
        raise ArquivoIlegivelError(f"Não foi possível ler '{caminho.name}': {exc}") from exc

    conteudo_base64 = base64.b64encode(conteudo_bruto).decode("utf-8")
    return ArquivoCarregado(caminho=caminho, mime_type=mime_type, conteudo_base64=conteudo_base64)


def carregar_par_avaliacao(
    caminho_gabarito: str | Path,
    caminho_prova_aluno: str | Path,
    settings: Settings,
) -> tuple[ArquivoCarregado, ArquivoCarregado]:
    """
    Falha rápido (fail-fast): se qualquer um dos dois arquivos tiver
    problema, nenhuma chamada ao agente é feita.
    """
    gabarito = carregar_arquivo(caminho_gabarito, settings)
    prova_aluno = carregar_arquivo(caminho_prova_aluno, settings)
    return gabarito, prova_aluno