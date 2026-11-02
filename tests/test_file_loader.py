"""
Testes de file_loader.py usando arquivos temporários (tmp_path do
pytest) — não dependem dos exemplos em data/examples nem de rede.
"""

import base64

import pytest

from feedbackai.config import Settings
from ingestion.file_loader import (
    ArquivoIlegivelError,
    ArquivoMuitoGrandeError,
    ArquivoNaoEncontradoError,
    ExtensaoNaoSuportadaError,
    carregar_arquivo,
    carregar_par_avaliacao,
)


@pytest.fixture
def settings() -> Settings:
    return Settings(google_api_key="fake-key-para-teste")


def test_carregar_arquivo_txt_ok(tmp_path, settings):
    caminho = tmp_path / "gabarito.txt"
    caminho.write_text("Questão 1: resposta esperada é x = 2", encoding="utf-8")

    resultado = carregar_arquivo(caminho, settings)

    assert resultado.mime_type == "text/plain"
    assert base64.b64decode(resultado.conteudo_base64).decode("utf-8") == (
        "Questão 1: resposta esperada é x = 2"
    )


def test_carregar_arquivo_gera_bloco_de_mensagem_correto(tmp_path, settings):
    caminho = tmp_path / "prova.txt"
    caminho.write_text("resposta do aluno", encoding="utf-8")

    resultado = carregar_arquivo(caminho, settings)
    bloco = resultado.como_bloco_mensagem()

    assert bloco["type"] == "media"
    assert bloco["mime_type"] == "text/plain"
    assert bloco["data"] == resultado.conteudo_base64


def test_arquivo_inexistente_levanta_erro(tmp_path, settings):
    caminho_inexistente = tmp_path / "nao_existe.pdf"

    with pytest.raises(ArquivoNaoEncontradoError):
        carregar_arquivo(caminho_inexistente, settings)


def test_extensao_nao_suportada_levanta_erro(tmp_path, settings):
    caminho = tmp_path / "prova.docx"
    caminho.write_text("conteudo qualquer", encoding="utf-8")

    with pytest.raises(ExtensaoNaoSuportadaError):
        carregar_arquivo(caminho, settings)


def test_arquivo_muito_grande_levanta_erro(tmp_path, settings):
    settings_limitado = Settings(
        google_api_key="fake-key-para-teste", tamanho_max_arquivo_mb=0
    )
    caminho = tmp_path / "gabarito.txt"
    caminho.write_text("a" * 2048, encoding="utf-8")

    with pytest.raises(ArquivoMuitoGrandeError):
        carregar_arquivo(caminho, settings_limitado)


def test_diretorio_nao_e_arquivo_valido(tmp_path, settings):
    with pytest.raises(ArquivoNaoEncontradoError):
        carregar_arquivo(tmp_path, settings)


def test_carregar_par_avaliacao(tmp_path, settings):
    gabarito_path = tmp_path / "gabarito.txt"
    prova_path = tmp_path / "prova.txt"
    gabarito_path.write_text("gabarito", encoding="utf-8")
    prova_path.write_text("prova do aluno", encoding="utf-8")

    gabarito, prova_aluno = carregar_par_avaliacao(gabarito_path, prova_path, settings)

    assert gabarito.caminho.name == "gabarito.txt"
    assert prova_aluno.caminho.name == "prova.txt"