# app_frontend_enem.py
from flask import Flask, render_template, jsonify, request, session
import requests
import json
import secrets

URL_BACKEND = "http://localhost:5000"
NOME_APP = "ENEM Helper - Interface Web"
CONFIANCA_MINIMA_RESPOSTA = 0.60

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

@app.route("/")
def pagina_inicial():
    session.pop("modo_pesquisa", None)
    session.pop("questoes_salvas", None)
    
    return render_template("index.html", nome_app=NOME_APP)

@app.route("/verificar_backend")
def verificar_backend():
    try:
        response = requests.get(f"{URL_BACKEND}/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            return jsonify({"disponivel": status.get("chatbot_disponivel") and status.get("banco_questoes_disponivel")})
        return jsonify({"disponivel": False})
    except Exception as e:
        print(f"Erro ao verificar backend: {e}")
        return jsonify({"disponivel": False, "erro": str(e)})

@app.route("/enviar_pergunta", methods=["POST"])
def enviar_pergunta():
    try:
        dados_req = request.json
        pergunta = dados_req.get("pergunta", "").strip()
        modo_pesquisa = session.get("modo_pesquisa", False)
        
        if pergunta.lower() in ['voltar', 'sair da pesquisa', 'cancelar pesquisa', 'modo normal', 'modo conversa']:
            session["modo_pesquisa"] = False
            return jsonify({
                "resposta": "Voltando ao modo de conversação normal. Como posso ajudar?",
                "questoes": [],
                "modo_pesquisa": False
            })
            
        if modo_pesquisa:
            
            palavras = pergunta.split()
            possivel_materia = palavras[0] if palavras else ""
            
            payload = {
                "consulta": pergunta,
                "materia": possivel_materia,
                "termos": " ".join(palavras[1:]) if len(palavras) > 1 else "",
                "limite": 5
            }
            
            response = requests.post(f"{URL_BACKEND}/pesquisar_questoes", json=payload, timeout=10)
            
            if response.status_code == 200:
                resultado = response.json()
                questoes = resultado.get("questoes", [])
                session["questoes_salvas"] = questoes  
                
                materia_encontrada = resultado.get("materia", "")
                termos_encontrados = resultado.get("termos", "")
                num_questoes = len(questoes)
                
                if questoes:
                    resposta_texto = f"Encontrei {num_questoes} questões"
                    if materia_encontrada:
                        resposta_texto += f" de {materia_encontrada}"
                    if termos_encontrados:
                        resposta_texto += f" relacionadas a '{termos_encontrados}'"
                    
                    resposta_texto += ".\n\nPara continuar pesquisando questões, digite outro termo ou matéria. Para voltar ao modo de conversa normal, digite 'voltar'."
                    
                    return jsonify({
                        "resposta": resposta_texto,
                        "questoes": questoes,
                        "modo_pesquisa": True 
                    })
                else:
                    sugestao = "\n\nTente outros termos ou uma matéria específica como 'Matemática', 'Linguagens', 'Ciências Humanas' ou 'Ciências da Natureza'.\n\nPara voltar ao modo de conversa normal, digite 'voltar'."
                    
                    return jsonify({
                        "resposta": f"Não encontrei questões com esses critérios.{sugestao}",
                        "questoes": [],
                        "modo_pesquisa": True 
                    })
            else:
                return jsonify({
                    "resposta": "Houve um erro ao pesquisar questões. Tente novamente.",
                    "questoes": [],
                    "modo_pesquisa": False
                })
        
        payload = {"pergunta": pergunta}
        response = requests.post(f"{URL_BACKEND}/responder", json=payload, timeout=10)
        
        if response.status_code == 200:
            resposta_obj = response.json()
            resposta_texto = resposta_obj.get("resposta", "")
            confianca = resposta_obj.get("confianca", 0)
            
            if resposta_obj.get("modo_pesquisa", False):
                session["modo_pesquisa"] = True
                return jsonify({
                    "resposta": resposta_texto,
                    "questoes": [],
                    "modo_pesquisa": True
                })
                
            if confianca >= CONFIANCA_MINIMA_RESPOSTA:
                return jsonify({
                    "resposta": resposta_texto,
                    "questoes": [],
                    "modo_pesquisa": False
                })
            else:
                mensagem_baixa_confianca = "Desculpe, não entendi bem sua pergunta. Você pode reformular ou perguntar sobre temas específicos do ENEM como datas, matérias ou dicas de estudo?"
                return jsonify({
                    "resposta": mensagem_baixa_confianca,
                    "questoes": [],
                    "modo_pesquisa": False
                })
        else:
            return jsonify({
                "resposta": "Desculpe, houve um problema ao processar sua pergunta.",
                "questoes": [],
                "modo_pesquisa": False
            })
    
    except Exception as e:
        print(f"Erro ao processar pergunta: {e}")
        return jsonify({
            "resposta": "Ocorreu um erro de comunicação com o serviço. Por favor, tente novamente mais tarde.",
            "questoes": [],
            "modo_pesquisa": False
        })

if __name__ == "__main__":
    print(f"=== INICIANDO INTERFACE WEB DO ENEM HELPER ===")
    print(f"Certifique-se de que o backend está em execução em {URL_BACKEND}")
    print("Iniciando servidor web na porta 5001...")
    app.run(host="0.0.0.0", port=5001, debug=True)