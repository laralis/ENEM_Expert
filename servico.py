from flask import Flask, Response, request, jsonify
from chatterbot import ChatBot
import json
import sqlite3
import traceback

from processar_questoes import (
    pesquisar_questoes,
    analisar_pergunta_usuario,
    formatar_questao,
    formatar_resposta,
    extrair_termos_pesquisa,
    normalizar_materia,
    BD_ENEM
)

NOME_ROBO = "ENEMExpert"
BD_ROBO_CHATTERBOT = "./chat.sqlite3"
CONFIANCA_MINIMA_RESPOSTA = 0.65
FRASE_RESPOSTA_ATIVAR_MODO_PESQUISA = "Qual matéria você gostaria de pesquisar questões (caso queira sair do modo pesquisa digite 'cancelar pesquisa'?"

app = Flask(NOME_ROBO)

INFO = {
    "nome": NOME_ROBO,
    "descricao": "API do Chatbot Assistente do ENEM - Ajuda estudantes a se prepararem para o ENEM",
    "versao": "1.0",
    "endpoints": {
        "/": "Informações sobre o serviço",
        "/status": "Verifica se o serviço está funcionando",
        "/responder": "Envia uma pergunta ao chatbot (POST)",
    }
}

def inicializar_chatbot():
    try:
        chatbot = ChatBot(
            NOME_ROBO,
            storage_adapter="chatterbot.storage.SQLStorageAdapter",
            database_uri=f"sqlite:///{BD_ROBO_CHATTERBOT}",
            read_only=True 
        )
        return True, chatbot
    except Exception as e:
        print(f"Erro ao inicializar o chatbot: {e}")
        return False, None

chatbot_inicializado, chatbot_instance = inicializar_chatbot()

@app.route("/")
def get_info():
    return jsonify(INFO)

@app.route("/status")
def get_status():
    status = {
        "chatbot_disponivel": chatbot_inicializado,
        "banco_questoes_disponivel": verificar_banco_questoes()
    }
    return jsonify(status)

def verificar_banco_questoes():
    try:
        conn = sqlite3.connect(BD_ENEM)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM questoes_enem")
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        print(f"Erro ao verificar banco de questões: {e}")
        return False

@app.route("/responder", methods=["POST"])
def responder_pergunta():
    if not chatbot_inicializado:
        return jsonify({"erro": "Chatbot não inicializado"}), 503
    
    try:
        conteudo = request.get_json()
        if not conteudo or "pergunta" not in conteudo:
            return jsonify({"erro": "Requisição inválida, 'pergunta' é obrigatória"}), 400
        
        pergunta = conteudo["pergunta"]
        
        comandos_pesquisa = [
            "pesquisar questões", "pesquisar questoes", "quero questões", "quero questoes", 
            "buscar questão", "buscar questao", "procurar exercício", "procurar exercicio",
            "mostrar questões", "mostrar questoes", "ver questões", "ver questoes",
            "preciso de questões", "preciso de questoes", "quero ver questões", "quero ver questoes",
            "me dê questões", "me de questoes", "mostre questões", "mostre questoes",
            "gostaria de ver questões", "gostaria de ver questoes"
        ]
        
        if any(cmd in pergunta.lower() for cmd in comandos_pesquisa):
            return jsonify({
                "resposta": FRASE_RESPOSTA_ATIVAR_MODO_PESQUISA,
                "confianca": 1.0,
                "modo_pesquisa": True
            })
        
        
        materias_diretas = ["matemática", "matematica", "linguagens", "português", "portugues", 
                         "ciências humanas", "ciencias humanas", "história", "historia", 
                         "geografia", "filosofia", "sociologia", "ciências da natureza", 
                         "ciencias da natureza", "física", "fisica", "química", "quimica", "biologia"]
        
        primeiro_termo = pergunta.lower().split()[0] if pergunta.strip() else ""
        if primeiro_termo in materias_diretas:
            materia, termos = analisar_pergunta_usuario(pergunta)
            if materia:  
                return jsonify({
                    "resposta": f"Buscando questões de {materia}...",
                    "confianca": 0.9,
                    "modo_pesquisa": True
                })
        
        resposta = chatbot_instance.get_response(pergunta)
        
        modo_pesquisa = resposta.text == FRASE_RESPOSTA_ATIVAR_MODO_PESQUISA
        
        if resposta.confidence < 0.4 and any(termo in pergunta.lower() for termo in ["questão", "questões", "exercício", "exercicios", "problema", "matéria"]):
            return jsonify({
                "resposta": "Não entendi completamente sua pergunta. Se você está procurando questões do ENEM, digite 'pesquisar questões' para ativar o modo de pesquisa.",
                "confianca": 0.5,
                "modo_pesquisa": False
            })
        
        return jsonify({
            "resposta": resposta.text,
            "confianca": resposta.confidence,
            "modo_pesquisa": modo_pesquisa
        })
    
    except Exception as e:
        print(f"Erro ao responder pergunta: {e}")
        traceback.print_exc()
        return jsonify({"erro": "Erro interno ao processar a pergunta"}), 500

@app.route("/pesquisar_questoes", methods=["POST"])
def buscar_questoes():
    try:
        conteudo = request.get_json()
        if not conteudo:
            return jsonify({"erro": "Requisição inválida"}), 400
        
        consulta = conteudo.get("consulta", "").strip()
        materia_direta = conteudo.get("materia", "").strip() if conteudo.get("materia") else ""
        termos_diretos = conteudo.get("termos", "").strip() if conteudo.get("termos") else ""
        limite = int(conteudo.get("limite", 10))  
        
        
        comandos_pesquisa = ["pesquisar questões", "quero questões", "buscar questão", "mostrar questões"]
        consulta_limpa = consulta.lower()
        for cmd in comandos_pesquisa:
            consulta_limpa = consulta_limpa.replace(cmd, "").strip()
        
        if "ciencias da natureza" in consulta_limpa or "ciências da natureza" in consulta_limpa:
            materia_normalizada = "Ciências da Natureza"
            termos = consulta_limpa.replace("ciencias da natureza", "").replace("ciências da natureza", "").strip()
        elif "ciencias humanas" in consulta_limpa or "ciências humanas" in consulta_limpa:
            materia_normalizada = "Ciências Humanas"
            termos = consulta_limpa.replace("ciencias humanas", "").replace("ciências humanas", "").strip()
        else:
            materia_normalizada = None
            termos = None
            
            if materia_direta:
                materia_normalizada = normalizar_materia(materia_direta)
                
                if termos_diretos:
                    termos = termos_diretos
                else:
                    termos = extrair_termos_pesquisa(consulta_limpa, materia_normalizada)
            
            else:
                materia_normalizada, termos = analisar_pergunta_usuario(consulta_limpa)
        
        
        questoes = pesquisar_questoes(materia_normalizada, termos, limite)
        
        if not questoes:
            
            if materia_normalizada and termos:
                questoes = pesquisar_questoes(materia_normalizada, "", limite)
            
            if not questoes and termos:
                questoes = pesquisar_questoes(None, termos, limite)
        
        resultados = []
        for q in questoes:
            resultados.append({
                "id": q["id"],
                "materia": q["materia"],
                "ano": q["ano"],
                "numero": q["numero_questao"],
                "pergunta": q["pergunta"],
                "alternativas": q["alternativas"],
                "resposta_correta": q["resposta_correta"],
                "explicacao": q["explicacao"],
                "formatada": formatar_questao(q)
            })
        
        return jsonify({
            "questoes": resultados,
            "materia": materia_normalizada or "",
            "termos": termos or "",
            "total_encontrado": len(resultados)
        })
    
    except Exception as e:
        print(f"Erro ao pesquisar questões: {e}")
        traceback.print_exc()
        return jsonify({"erro": "Erro interno ao pesquisar questões"}), 500


if __name__ == "__main__":
    print(f"=== INICIANDO SERVIÇO BACKEND DO {NOME_ROBO} ===")
    if not chatbot_inicializado:
        print("AVISO: Chatbot não inicializado corretamente. Verifique se o treinamento foi executado.")
    
    if not verificar_banco_questoes():
        print("AVISO: Banco de questões não encontrado ou vazio. Execute o script processar_questoes.py primeiro.")
    
    print(f"Serviço ativo na porta 5000. Acesse http://localhost:5000 para obter informações sobre a API.")
    app.run(host="0.0.0.0", port=5000, debug=True)