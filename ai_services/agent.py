# import os
# from dotenv import load_dotenv
# from langchain_google_genai import ChatGoogleGenerativeAI

# load_dotenv()

# # Inicializa o Gemini gratuitamente com o modelo mais recente
# llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)

# resposta = llm.invoke("Responda em uma frase: qual a função de um professor?")
# print(resposta.content)

import os
import warnings
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

# Desativa avisos não críticos de bibliotecas internas
warnings.filterwarnings("ignore")

load_dotenv()

# 1. Definimos a estrutura exata que queremos que a IA devolva (JSON)
class AvaliacaoQuestao(BaseModel):
    nota: float = Field(description="A nota final da questão, de 0.0 a 10.0")
    criterios_atendidos: list[str] = Field(description="Quais critérios do gabarito foram cumpridos pela resposta")
    criterios_falhos: list[str] = Field(description="Quais critérios do gabarito faltaram na resposta")
    feedback_aluno: str = Field(description="Mensagem educativa e construtiva para o aluno")

def testar_agente_correcao():
    print("Iniciando o modelo de correção...")
    
    # Inicializa o Gemini
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)
    
    # 2. Forçamos o modelo a responder respeitando a classe AvaliacaoQuestao
    llm_estruturado = llm.with_structured_output(AvaliacaoQuestao)
    
    # 3. Montamos o prompt de teste (mais tarde, passaremos isso dinamicamente)
    gabarito = "O aluno deve explicar que a mitocôndria é responsável pela respiração celular e produção de energia (ATP)."
    resposta_aluno = "A mitocôndria é a parte da célula que cria energia."
    
    mensagem = f"""Você é um professor rigoroso. Avalie a resposta do aluno com base no gabarito.
    
    Gabarito: {gabarito}
    Resposta do Aluno: {resposta_aluno}
    """
    
    print("\nAvaliando a resposta do aluno...\n")
    
    # 4. Invocamos o modelo estruturado
    resultado = llm_estruturado.invoke(mensagem)
    
    # 5. Imprimimos o resultado de forma limpa, acessando os atributos do objeto
    print(f"Nota Final: {resultado.nota}")
    print(f"Feedback: {resultado.feedback_aluno}")
    print("\nCritérios:")
    print(f"- Atendidos: {', '.join(resultado.criterios_atendidos)}")
    print(f"- Faltantes: {', '.join(resultado.criterios_falhos)}")

if __name__ == "__main__":
    testar_agente_correcao()