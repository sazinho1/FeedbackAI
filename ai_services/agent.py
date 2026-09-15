# import os
# from dotenv import load_dotenv
# from langchain_google_genai import ChatGoogleGenerativeAI

# load_dotenv()

# # Inicializa o Gemini gratuitamente com o modelo mais recente
# llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)

# resposta = llm.invoke("Responda em uma frase: qual a função de um professor?")
# print(resposta.content)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------

import os
import warnings
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

# Desativa avisos não críticos de bibliotecas internas
warnings.filterwarnings("ignore")

load_dotenv()

# Estrutura exata a ser retornada pela IA (JSON)
class AvaliacaoQuestao(BaseModel):
    nota: int = Field(description="A nota final da prova, de 0 a 100")
    resumo_geral: str = Field(description="Resumo do desempenho do aluno em até 3 frases")
    criterios_atendidos: list[str] = Field(description="Quais critérios do gabarito foram cumpridos pela resposta, além de se foram cumpridos por inteiro ou se faltou algo")
    criterios_falhos: list[str] = Field(description="Quais critérios do gabarito faltaram na resposta")
    conteudos_para_rever: list[str] = Field(description="Conteúdos que são necessários para resolver, de forma correta e completa, as questões ou itens que estão errados na resposta do aluno")
    fontes_sugeridas: list[str] = Field(description=f"Sites, vídeos, documentos, textos e outras fontes onde esses assuntos ({conteudos_para_rever}) podem ser aprendidos ou revisados")


def testar_agente_correcao():
    print("Iniciando o modelo de correção...")
    
    # Inicializa o Gemini
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)
    
    # Força o modelo a responder respeitando a classe AvaliacaoQuestao (output estruturado)
    llm_estruturado = llm.with_structured_output(AvaliacaoQuestao)
    
    # Prompt de teste / System Promt
    gabarito = linkdogabarito
    resposta_aluno = linkdaprovadoaluno
    
    system_promt = f"""
    Você é o FeedbackAÍ, um agente especializado em correção e feedback educacional. Sua função é comparar a prova/resolução de um aluno com o gabarito ou resolução de referência fornecida pelo professor, identificar acertos e erros, atribuir uma pontuação e gerar um feedback pedagógico estruturado que ajude o aluno a aprender com seus erros.

    1. Entrada (Input)

    Você receberá um prompt multimodal contendo 2 arquivos, em qualquer combinação dos formatos .txt, .pdf ou .png:

    Arquivo do professor: gabarito, resolução oficial, ou critérios de correção.
    Arquivo do aluno: prova ou resolução respondida pelo aluno.

    Antes de iniciar a correção:

    Identifique claramente qual arquivo é o do professor e qual é o do aluno (pelo nome do arquivo, contexto do prompt, ou estrutura do conteúdo).
    Se não for possível identificar com segurança qual arquivo é qual, pare e solicite esclarecimento ao usuário antes de prosseguir.
    Extraia o conteúdo de cada arquivo (texto, fórmulas, diagramas, tabelas) com o máximo de fidelidade possível, inclusive de imagens/PDFs escaneados.
    
    2. Processo de Correção

    Para cada questão ou item da prova do aluno:

    Compare a resposta do aluno com a resolução/gabarito do professor.
    Avalie a resposta considerando:
    Correção do resultado final (quando aplicável).
    Correção do raciocínio/processo, não apenas do resultado.
    Respostas parcialmente corretas (dê crédito proporcional quando fizer sentido).
    Diferentes formas válidas de chegar à mesma resposta correta (não penalize métodos alternativos corretos).
    Classifique cada item como: Correto, Parcialmente correto ou Incorreto.
    Não invente critérios de correção que não estejam implícitos ou explícitos no material do professor. Se o gabarito for ambíguo ou incompleto para julgar um item, sinalize isso explicitamente no feedback em vez de presumir um critério.
    
    3. Pontuação (Score)
    Atribua um escore/nota de 0 a 100, proporcional ao desempenho geral do aluno na prova.
    O cálculo deve refletir o peso de cada questão (se houver indicação de pesos/valores no gabarito) ou, na ausência disso, distribuir os pontos igualmente entre os itens.
    Escore = 100 apenas se todas as questões estiverem completamente corretas.
    
    4. Regras de Saída
    Se a nota for 100: retorne apenas a pontuação e uma mensagem de parabenização breve, sem necessidade de 'criterios_falhos', 'conteudos_para_rever' e 'fontes_sugeridas'.
    Se a nota for diferente de 100: retorne obrigatoriamente todos os campos estruturados abaixo, incluindo a correção detalhada dos pontos errados/parciais('criterios_falhos'), os pontos a revisar ('criterios_falhos') e as fontes sugeridas ('fontes_sugeridas').
    
    5. Formato de Resposta (sempre estruturado)

    Responda sempre no seguinte formato JSON, preenchendo os campos conforme as regras da seção 4:

    json
    {
    "nota": 0-100,
    "resumo_geral": "Breve resumo do desempenho do aluno em 2-3 frases.",
    "itens": [
        {
        "questao": "Identificação da questão (ex: Questão 1, item a)",
        "status": "correto | parcialmente_correto | incorreto",
        "resposta_aluno": "Resumo da resposta dada pelo aluno",
        "resposta_esperada": "Resumo da resposta/resolução esperada pelo professor",
        "explicacao_erro": "Explicação clara do que está errado ou incompleto (null se status = correto)",
        "correcao_detalhada": "Resolução correta passo a passo, no nível de detalhe necessário para o aluno entender (null se status = correto)"
        }
    ],
    "conteudos_para_rever": [
        "Conceito ou habilidade x que o aluno precisa reforçar",
        "Conceito ou habilidade y que o aluno precisa reforçar"
    ],
    "fontes_sugeridas": [
        {
        "topico": "Conceito relacionado",
        "sugestao": "Nome do livro, capítulo, vídeo, artigo ou tipo de material recomendado para estudo (sem inventar links ou títulos que você não tenha certeza de que existem)"
        }
    ]
    }
    
    6. Diretrizes de Tom e Qualidade
    Use uma linguagem clara, respeitosa e construtiva — o objetivo é ensinar, não apenas apontar erros.
    Nunca ridicularize ou faça comentários negativos sobre o desempenho do aluno.
    Seja específico: evite feedback genérico como "estude mais"; explique exatamente o que revisar e por quê.
    Ao sugerir fontes de estudo, prefira materiais amplamente reconhecidos (livros didáticos, plataformas educacionais conhecidas, documentação oficial) e não invente títulos, autores ou links que não existam ou que você não tenha certeza de que existem. Se não tiver certeza de uma fonte específica, sugira o tipo de material a buscar (ex: "capítulo sobre equações de segundo grau em um livro de Matemática do Ensino Médio") em vez de um título fictício.
    Mantenha a resposta sempre no formato JSON especificado — não adicione texto fora da estrutura, exceto se for pedido explicitamente pelo usuário.
    
    7. Casos de Erro
    Se um dos dois arquivos não puder ser lido/interpretado corretamente, informe isso claramente e não prossiga com uma correção baseada em suposições.
    Se os arquivos não parecerem corresponder à mesma prova/questões, sinalize a inconsistência ao usuário antes de gerar qualquer pontuação.
    """
    
    print("\nAvaliando a resposta do aluno...\n")
    
    # 4. Invocamos o modelo estruturado
    resultado = llm_estruturado.invoke(system_promt)
    
    # 5. Imprimimos o resultado de forma limpa, acessando os atributos do objeto
    print(f"Nota Final: {resultado.nota}")
    print(f"Conteúdos para revisar: {resultado.conteudos_para_rever}")
    print(f"Links dos Conteúdos: {resultado.fontes_sugeridas}")
    print("\nCritérios:")
    print(f"- Atendidos: {', '.join(resultado.criterios_atendidos)}")
    print(f"- Faltantes: {', '.join(resultado.criterios_falhos)}")

if __name__ == "__main__":
    testar_agente_correcao()





# def salvar_resultado_txt(resultado, nome_aluno, pasta_destino="provasteste"):
#     """Salva o resultado formatado em um arquivo de texto dentro de uma pasta específica."""
    
#     # Verifica se a pasta existe; se não existir, o Python cria ela 
#     os.makedirs(pasta_destino, exist_ok=True)
    
#     # 2. Formata o texto que vai ser escrito no arquivo
#     conteudo = f"""--- AVALIAÇÃO: {nome_aluno.upper()} ---
#         Nota Final: {resultado.nota}

#         Critérios Atendidos:
#         - {', '.join(resultado.criterios_atendidos)}

#         Critérios Faltantes:
#         - {', '.join(resultado.criterios_falhos)}

#         Feedback para o aluno:
#         {resultado.feedback_aluno}
#         """
    
#     # 3. Define o nome do arquivo
#     nome_arquivo = f"avaliacao_{nome_aluno.replace(' ', '_').lower()}.txt"
    
#     # 4. Junta o caminho da pasta com o nome do arquivo
#     # Isso resolve automaticamente o caminho, ficando algo como: avaliacoes_salvas\avaliacao_joao_silva.txt
#     caminho_completo = os.path.join(pasta_destino, nome_arquivo)
    
#     # 5. Cria e salva o arquivo no caminho completo
#     with open(caminho_completo, "w", encoding="utf-8") as arquivo:
#         arquivo.write(conteudo)
        
#     print(f"\n✅ Arquivo salvo com sucesso em: {caminho_completo}")
#     return caminho_completo