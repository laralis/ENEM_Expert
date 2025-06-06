import requests
import json
import os
import sys
from time import sleep

URL_BACKEND = "http://localhost:5000"
NOME_ROBO = "ENEMExpert"

ESTADO_NORMAL = 0
ESTADO_PESQUISA = 1

FRASE_RESPOSTA_ATIVAR_MODO_PESQUISA = "Qual matéria você gostaria de pesquisar questões (caso queira sair do modo pesquisa digite 'cancelar pesquisa'?"

def enviar_pergunta(pergunta):
    try:
        payload = {"pergunta": pergunta}
        response = requests.post(f"{URL_BACKEND}/responder", json=payload, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro ao enviar pergunta: Status {response.status_code}")
            return {"resposta": "Ocorreu um erro ao processar sua pergunta.", "confianca": 0, "modo_pesquisa": False}
    except Exception as e:
        print(f"Erro na comunicação com o backend: {e}")
        return {"resposta": "Não foi possível contactar o serviço de resposta.", "confianca": 0, "modo_pesquisa": False}

def pesquisar_questoes(consulta, limite=10):
    try:
        consulta_lower = consulta.lower()
        if "ciências da natureza" in consulta_lower or "ciencias da natureza" in consulta_lower:
            materia = "Ciências da Natureza"
            termos = consulta_lower.replace("ciências da natureza", "").replace("ciencias da natureza", "").strip()
        elif "ciências humanas" in consulta_lower or "ciencias humanas" in consulta_lower:
            materia = "Ciências Humanas"
            termos = consulta_lower.replace("ciências humanas", "").replace("ciencias humanas", "").strip()
        elif "," in consulta:
            partes = consulta.split(",", 1)
            materia = partes[0].strip()
            termos = partes[1].strip() if len(partes) > 1 else ""
        else:
            palavras = consulta.split()
            primeira_palavra = palavras[0].lower() if palavras else ""
            
            materias_comuns = [
                "matemática", "matematica", "mat", "português", "portugues", "port",
                "história", "historia", "hist", "geografia", "geo", "biologia", "bio",
                "física", "fisica", "fis", "química", "quimica", "quim", "linguagens", 
                "humanas", "natureza", "filosofia", "filo", "sociologia", "socio",
                "inglês", "ingles"
            ]
            
            if primeira_palavra in materias_comuns:
                materia = primeira_palavra
                termos = " ".join(palavras[1:])
            else:
                materia = ""
                termos = consulta
        
        payload = {
            "consulta": consulta,
            "materia": materia,
            "termos": termos,
            "limite": limite
        }
        
        response = requests.post(f"{URL_BACKEND}/pesquisar_questoes", json=payload, timeout=10)
        
        if response.status_code == 200:
            resultado = response.json()
            print(f"Resposta recebida: {len(resultado.get('questoes', []))} questões encontradas")
            return resultado
        else:
            print(f"Erro ao pesquisar questões: Status {response.status_code}")
            return {"questoes": [], "total_encontrado": 0, "materia": materia, "termos": termos}
    except Exception as e:
        print(f"Erro na comunicação com o backend: {e}")
        return {"questoes": [], "total_encontrado": 0, "materia": "", "termos": ""}


def executar_chat_console():
    print(f"=== {NOME_ROBO} - Assistente de Estudos para o ENEM ===")
    print("Digite suas perguntas ou 'sair' para encerrar o programa.")
    print("Você pode solicitar questões do ENEM usando 'pesquisar questões' ou similar.")
    print("-" * 60)
    
    estado_atual = ESTADO_NORMAL
    questoes_atuais = []
    indice_questao_atual = -1
    
    while True:
        try:
            if estado_atual == ESTADO_NORMAL:
                pergunta_usuario = input("👤 Você: ")
            else:
                pergunta_usuario = input("👤 Você (modo pesquisa): ")
            
            if pergunta_usuario.strip().lower() == 'sair':
                print(f"🤖 {NOME_ROBO}: Encerrando. Até a próxima!")
                break
            
            if not pergunta_usuario.strip():
                continue
            
            comandos_pesquisa = ["pesquisar questões", "quero questões", "buscar questão", "procurar exercício", 
                                "mostrar questões", "ver questões", "nova pesquisa", "outra matéria"]
                                
            if any(cmd in pergunta_usuario.lower() for cmd in comandos_pesquisa):
                print(f"🤖 {NOME_ROBO}: {FRASE_RESPOSTA_ATIVAR_MODO_PESQUISA}")
                estado_atual = ESTADO_PESQUISA
                questoes_atuais = [] 
                indice_questao_atual = -1
                continue
            
            if estado_atual == ESTADO_NORMAL:
                resposta_obj = enviar_pergunta(pergunta_usuario)
                
                if resposta_obj.get("modo_pesquisa"):
                    estado_atual = ESTADO_PESQUISA
                    print(f"🤖 {NOME_ROBO}: {resposta_obj.get('resposta')}")
                elif resposta_obj.get('confianca', 0) >= 0.6:
                    print(f"🤖 {NOME_ROBO}: {resposta_obj.get('resposta')}")
                    if 'confianca' in resposta_obj:
                        print(f"   [Confiança: {resposta_obj.get('confianca'):.2f}]")
                else:
                    print(f"🤖 {NOME_ROBO}: Desculpe, não entendi bem sua pergunta. Você pode reformular ou perguntar sobre o ENEM, ou digitar 'pesquisar questões' para buscar questões específicas.")
            
            elif estado_atual == ESTADO_PESQUISA:
                pergunta_lower = pergunta_usuario.lower()
                
                comandos_voltar = [
                    'voltar', 'sair da pesquisa', 'cancelar pesquisa', 'modo normal', 
                    'sair do modo pesquisa', 'conversa normal', 'voltar ao chat', 
                    'quero conversar', 'conversar', 'parar pesquisa', 'encerrar pesquisa'
                ]
                
                if any(cmd == pergunta_lower for cmd in comandos_voltar):
                    print(f"🤖 {NOME_ROBO}: Voltando ao modo normal de conversa. Como posso ajudar?")
                    estado_atual = ESTADO_NORMAL
                    questoes_atuais = []
                    indice_questao_atual = -1
                    continue
                
                if pergunta_lower in ['resposta', 'ver resposta', 'mostrar resposta', 'explicação', 'gabarito', 'solucao', 'solução'] and questoes_atuais:
                    if 0 <= indice_questao_atual < len(questoes_atuais):
                        questao = questoes_atuais[indice_questao_atual]
                        print(f"\n✅ A resposta correta é a alternativa {questao.get('resposta_correta')}.")
                        print(f"\n📚 Explicação: {questao.get('explicacao')}\n")
                    else:
                        print(f"🤖 {NOME_ROBO}: Não há questão selecionada para mostrar a resposta.")
                    continue
                
                if pergunta_lower in ['próxima', 'proxima', 'próxima questão', 'proxima questao', 'seguinte', 'outra', 'avançar', 'avancar'] and questoes_atuais:
                    if questoes_atuais and indice_questao_atual < len(questoes_atuais) - 1:
                        indice_questao_atual += 1
                        questao = questoes_atuais[indice_questao_atual]
                        print(questao.get('formatada', ''))
                    else:
                        print(f"🤖 {NOME_ROBO}: Não há mais questões disponíveis. Tente uma nova pesquisa ou digite 'voltar' para sair do modo pesquisa.")
                    continue
                
                if pergunta_lower in ['anterior', 'questão anterior', 'questao anterior', 'voltar questão', 'voltar questao', 'retornar'] and questoes_atuais:
                    if questoes_atuais and indice_questao_atual > 0:
                        indice_questao_atual -= 1
                        questao = questoes_atuais[indice_questao_atual]
                        print(questao.get('formatada', ''))
                    else:
                        print(f"🤖 {NOME_ROBO}: Não há questões anteriores disponíveis.")
                    continue
                
                print(f"🤖 {NOME_ROBO}: Pesquisando questões sobre '{pergunta_usuario}'...")
                
                resultado = pesquisar_questoes(pergunta_usuario)
                
                questoes_atuais = resultado.get("questoes", [])
                total_encontrado = len(questoes_atuais)
                materia_encontrada = resultado.get("materia", "")
                termos_encontrados = resultado.get("termos", "")
                
                if total_encontrado > 0:
                    resposta_formatada = f"Encontrei {total_encontrado} questões"
                    
                    if materia_encontrada:
                        resposta_formatada += f" de {materia_encontrada}"
                    
                    if termos_encontrados:
                        resposta_formatada += f" sobre '{termos_encontrados}'"
                    
                    print(f"🤖 {NOME_ROBO}: {resposta_formatada}! Mostrando a primeira:")
                    indice_questao_atual = 0
                    questao_atual = questoes_atuais[indice_questao_atual]
                    print(questao_atual.get('formatada', ''))
                    print("\nDigite 'resposta' para ver a solução ou 'próxima' para ver outra questão.")
                    print("Para uma nova pesquisa, basta digitar a matéria e/ou assunto desejado.")
                    print("Para voltar ao modo de conversação normal, digite 'voltar'.")
                else:
                    sugestoes = ""
                    if materia_encontrada:
                        sugestoes = f"\nTente outros termos em '{materia_encontrada}' ou experimente apenas o nome da matéria."
                    else:
                        sugestoes = "\nTente ser mais específico, como 'Matemática equações' ou 'História revolução industrial'."
                    
                    print(f"🤖 {NOME_ROBO}: Não encontrei questões com esses critérios.{sugestoes}")
                    print("Para voltar ao modo de conversação normal, digite 'voltar'.")
        
        except KeyboardInterrupt:
            print(f"\n\n🤖 {NOME_ROBO}: Programa interrompido pelo usuário. Até a próxima!")
            break
        
        except Exception as e:
            print(f"\n⚠️ Ocorreu um erro: {e}")
            print("Tente novamente ou digite 'sair' para encerrar.")

if __name__ == "__main__":

    executar_chat_console()