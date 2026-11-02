"""
Testes do schema de saída. Não precisam de API key nem de rede — são a
primeira linha de defesa contra o schema divergir da lógica de negócio
(foi um schema mal alinhado que causou o bug original do projeto).
"""

import pytest
from pydantic import ValidationError

from schemas.avaliacao import AvaliacaoQuestao, FonteSugerida, ItemAvaliado


def test_avaliacao_minima_valida():
    avaliacao = AvaliacaoQuestao(nota=100, resumo_geral="Prova impecável, parabéns!")

    assert avaliacao.nota == 100
    # Campos de detalhamento devem ter default vazio, não obrigar o
    # chamador a preenchê-los manualmente no caso de nota 100.
    assert avaliacao.itens == []
    assert avaliacao.conteudos_para_rever == []
    assert avaliacao.fontes_sugeridas == []


@pytest.mark.parametrize("nota_invalida", [-1, 101, 1000])
def test_nota_fora_do_intervalo_e_rejeitada(nota_invalida):
    with pytest.raises(ValidationError):
        AvaliacaoQuestao(nota=nota_invalida, resumo_geral="qualquer coisa")


def test_item_avaliado_aceita_status_valido():
    item = ItemAvaliado(
        questao="Questão 1",
        status="parcialmente_correto",
        resposta_aluno="x = 2",
        resposta_esperada="x = 2 ou x = -2",
        explicacao_erro="Faltou considerar a raiz negativa.",
        correcao_detalhada="x² = 4 implica x = ±2, então x = 2 ou x = -2.",
    )
    assert item.status == "parcialmente_correto"


def test_item_avaliado_rejeita_status_invalido():
    with pytest.raises(ValidationError):
        ItemAvaliado.model_validate({
            "questao": "Questão 1",
            "status": "quase_certo",  # não está no Literal permitido
            "resposta_aluno": "x = 2",
            "resposta_esperada": "x = 2 ou x = -2",
        })


def test_avaliacao_completa_com_itens_e_fontes():
    avaliacao = AvaliacaoQuestao(
        nota=70,
        resumo_geral="Bom domínio de Bhaskara, mas atenção às raízes negativas.",
        itens=[
            ItemAvaliado(
                questao="Questão 2",
                status="parcialmente_correto",
                resposta_aluno="x = 2",
                resposta_esperada="x = 2 ou x = -2",
                explicacao_erro="Faltou a raiz negativa.",
                correcao_detalhada="x² = 4 → x = ±2.",
            )
        ],
        conteudos_para_rever=["Raízes de equações do tipo x² = k"],
        fontes_sugeridas=[
            FonteSugerida(
                topico="Equações do 2º grau incompletas",
                sugestao="Capítulo sobre equações incompletas em um livro de Matemática do Ensino Fundamental.",
            )
        ],
    )

    assert avaliacao.itens[0].status == "parcialmente_correto"
    assert avaliacao.fontes_sugeridas[0].topico.startswith("Equações")