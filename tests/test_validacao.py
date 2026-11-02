import pytest

from feedbackai.config import Settings
from ingestion.file_loader import carregar_arquivo
from schemas.avaliacao import AvaliacaoQuestao, ItemAvaliado
from utils.validacao import (
    ArquivosInconsistentesError,
    verificar_arquivos_distintos,
    verificar_resultado_avaliacao,
)


@pytest.fixture
def settings() -> Settings:
    return Settings(google_api_key="fake-key-para-teste")


def test_arquivos_identicos_levantam_erro(tmp_path, settings):
    caminho_a = tmp_path / "a.txt"
    caminho_b = tmp_path / "b.txt"
    caminho_a.write_text("mesmo conteudo", encoding="utf-8")
    caminho_b.write_text("mesmo conteudo", encoding="utf-8")

    arquivo_a = carregar_arquivo(caminho_a, settings)
    arquivo_b = carregar_arquivo(caminho_b, settings)

    with pytest.raises(ArquivosInconsistentesError):
        verificar_arquivos_distintos(arquivo_a, arquivo_b)


def test_arquivos_diferentes_nao_levantam_erro(tmp_path, settings):
    caminho_a = tmp_path / "gabarito.txt"
    caminho_b = tmp_path / "prova.txt"
    caminho_a.write_text("gabarito", encoding="utf-8")
    caminho_b.write_text("resposta do aluno", encoding="utf-8")

    arquivo_a = carregar_arquivo(caminho_a, settings)
    arquivo_b = carregar_arquivo(caminho_b, settings)

    verificar_arquivos_distintos(arquivo_a, arquivo_b)  # não deve levantar


def test_nota_100_com_itens_preenchidos_gera_aviso():
    avaliacao = AvaliacaoQuestao(
        nota=100,
        resumo_geral="Parabéns!",
        itens=[
            ItemAvaliado(
                questao="Questão 1",
                status="correto",
                resposta_aluno="x = 2",
                resposta_esperada="x = 2",
            )
        ],
    )

    avisos = verificar_resultado_avaliacao(avaliacao)

    assert any("itens" in aviso for aviso in avisos)


def test_nota_100_limpa_nao_gera_aviso():
    avaliacao = AvaliacaoQuestao(nota=100, resumo_geral="Parabéns!")

    avisos = verificar_resultado_avaliacao(avaliacao)

    assert avisos == []


def test_nota_menor_que_100_sem_itens_gera_aviso():
    avaliacao = AvaliacaoQuestao(nota=70, resumo_geral="Bom, mas com pontos a revisar.")

    avisos = verificar_resultado_avaliacao(avaliacao)

    assert any("itens" in aviso for aviso in avisos)


def test_item_incorreto_sem_explicacao_gera_aviso():
    avaliacao = AvaliacaoQuestao(
        nota=50,
        resumo_geral="Alguns erros a corrigir.",
        itens=[
            ItemAvaliado(
                questao="Questão 3",
                status="incorreto",
                resposta_aluno="x = 5",
                resposta_esperada="x = -1",
                explicacao_erro=None,
            )
        ],
        conteudos_para_rever=["Delta igual a zero"],
    )

    avisos = verificar_resultado_avaliacao(avaliacao)

    assert any("explicacao_erro" in aviso for aviso in avisos)