import logging
import sys

from core.agente_correcao import AgenteCorrecao
from feedbackai.config import ConfiguracaoInvalidaError, carregar_configuracoes
from ingestion.file_loader import (
    ArquivoIlegivelError,
    ArquivoMuitoGrandeError,
    ArquivoNaoEncontradoError,
    ExtensaoNaoSuportadaError,
)
from utils.validacao import ArquivosInconsistentesError

logging.basicConfig(level=logging.INFO)


def main():
    try:
        settings = carregar_configuracoes()
        agente = AgenteCorrecao(settings)

            """tem que arrumar um jeito pra o usuario colocar esse input"""
        resultado = agente.avaliar(
            caminho_gabarito=,
            caminho_prova_aluno=,
        )
    except ConfiguracaoInvalidaError as exc:
        sys.exit(f"Erro de configuração: {exc}")
    except (
        ArquivoNaoEncontradoError,
        ExtensaoNaoSuportadaError,
        ArquivoMuitoGrandeError,
        ArquivoIlegivelError,
        ArquivosInconsistentesError,
    ) as exc:
        sys.exit(f"Erro nos arquivos de entrada: {exc}")

    avaliacao = resultado.avaliacao

    print(f"Nota: {avaliacao.nota}")
    print(f"Resumo: {avaliacao.resumo_geral}")

    for item in avaliacao.itens:
        print(f"\n{item.questao}: {item.status}")
        if item.explicacao_erro:
            print(f"  Erro: {item.explicacao_erro}")

    if avaliacao.conteudos_para_rever:
        print("\nConteúdos para rever:")
        for conteudo in avaliacao.conteudos_para_rever:
            print(f"- {conteudo}")

    if avaliacao.fontes_sugeridas:
        print("\nFontes sugeridas:")
        for fonte in avaliacao.fontes_sugeridas:
            print(f"- {fonte.topico}: {fonte.sugestao}")

    if resultado.avisos:
        print("\nAvisos de consistência:")
        for aviso in resultado.avisos:
            print(f"- {aviso}")


if __name__ == "__main__":
    main()