from feedbackai.config import carregar_configuracoes
from core.agente_correcao import AgenteCorrecao


def testar_agente_correcao():
    print("Iniciando o modelo de correção...")
    agente = AgenteCorrecao(carregar_configuracoes())

    print("\nAvaliando a prova...")
    resultado = agente.avaliar(
        caminho_gabarito="data/examples/historia_gabarito.txt",
        caminho_prova_aluno="data/examples/historia_prova_aluno.txt",
    )

    avaliacao = resultado.avaliacao
    print(f"Nota Final: {avaliacao.nota}")
    print(f"Resumo: {avaliacao.resumo_geral}")
    print(f"Conteúdos para revisar: {avaliacao.conteudos_para_rever}")
    print(f"Fontes sugeridas: {avaliacao.fontes_sugeridas}")

    print("\nItens:")
    for item in avaliacao.itens:
        print(f"- {item.questao}: {item.status}")

    if resultado.avisos:
        print("\nAvisos:", resultado.avisos)

'''isto é, se esse arquivo está sendo executado diretamente, rode o código abaixo'''
if __name__ == "__main__": 
    testar_agente_correcao()