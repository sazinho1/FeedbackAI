"""
Configurações centralizadas do FeedbackAÍ.

Por que um módulo de config separado:
- Evita "magic values" (nome do modelo, temperature, limites de arquivo)
  espalhados pelo código — tudo em um único lugar facilita pra auditar e mudar.
- Valida na inicialização (fail-fast): se faltar uma variável de ambiente
  obrigatória, o erro aparece de forma clara ao subir a aplicação, não no
  meio de uma correção de prova.
- Permite trocar comportamento por ambiente (dev/teste/produção) sem
  tocar em lógica de negócio.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv


load_dotenv()


class ConfiguracaoInvalidaError(Exception):
    """Levantada quando uma variável de ambiente obrigatória está ausente ou inválida."""


# Extensões e mime types que o pipeline de ingestão sabe processar.
# Centralizado aqui porque tanto o file_loader quanto a validacao
# precisam dessa mesma lista (evita duas fontes de verdade divergindo).
MIME_TYPES_SUPORTADOS: dict[str, str] = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".txt": "text/plain",
}


@dataclass(frozen=True)
class Settings:
    google_api_key: str
    model_name: str = "gemini-3.5-flash"
    temperature: float = 0.0
    max_retries: int = 2
    timeout_segundos: int = 60

    # Limite de tamanho por arquivo enviado (evita estourar payload/custo por acidente).
    tamanho_max_arquivo_mb: int = 20

    extensoes_suportadas: tuple[str, ...] = field(
        default_factory=lambda: tuple(MIME_TYPES_SUPORTADOS.keys())
    )

    @property
    def tamanho_max_arquivo_bytes(self) -> int:
        return self.tamanho_max_arquivo_mb * 1024 * 1024


def carregar_configuracoes() -> Settings:
    """
    Lê e valida as variáveis de ambiente, retornando um objeto Settings imutável.

    Levanta ConfiguracaoInvalidaError com uma mensagem clara caso algo
    obrigatório esteja faltando.
    """
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ConfiguracaoInvalidaError(
            "GOOGLE_API_KEY (ou GEMINI_API_KEY) não encontrada. "
            "Defina essa variável no arquivo .env antes de rodar o agente."
        )

    model_name = os.getenv("FEEDBACKAI_MODEL", "gemini-3.5-flash")

    temperature_raw = os.getenv("FEEDBACKAI_TEMPERATURE", "0.0")
    try:
        temperature = float(temperature_raw)
    except ValueError as exc:
        raise ConfiguracaoInvalidaError(
            f"FEEDBACKAI_TEMPERATURE inválida: {temperature_raw!r} não é um número."
        ) from exc

    return Settings(
        google_api_key=api_key,
        model_name=model_name,
        temperature=temperature,
    )