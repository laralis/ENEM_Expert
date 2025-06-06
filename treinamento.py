from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer 
import json
import os
import logging

NOME_ROBO = "ENEMExpert"
BD_ROBO_CHATTERBOT = "./chat.sqlite3"
ARQUIVOS_JSON_CONVERSAS = [
    "./conversas/saudacoes.json",
    "./conversas/informacoes_basicas.json",
    "./conversas/comandos_pesquisa.json"  
]

def inicializar_robo():
    print(f"Inicializando o robô '{NOME_ROBO}'...")
    db_uri = f'sqlite:///{BD_ROBO_CHATTERBOT}'

    if os.path.exists(BD_ROBO_CHATTERBOT):
        try:
            print(f"Removendo banco de dados existente: {BD_ROBO_CHATTERBOT}")
            os.remove(BD_ROBO_CHATTERBOT)
        except OSError as e:
            print(f"Erro ao remover banco de dados: {e}")

    try:
        robo_instance = ChatBot(
            NOME_ROBO,
            storage_adapter='chatterbot.storage.SQLStorageAdapter',
            database_uri=db_uri
        )
        print(f"Robô '{NOME_ROBO}' instanciado com sucesso.")
        return True, robo_instance
    except Exception as e:
        print(f"ERRO ao inicializar o robô: {e}")
        return False, None

def carregar_conversas_json(arquivos_json_paths):
    todas_as_conversas = []
    print("Carregando conversas dos arquivos JSON...")
    
    for caminho_arquivo in arquivos_json_paths:
        try:
            with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
                if "conversas" in dados and isinstance(dados["conversas"], list):
                    for bloco in dados["conversas"]:
                        if "mensagens" in bloco and "resposta" in bloco and isinstance(bloco["mensagens"], list):
                            resposta_bloco = bloco["resposta"]
                            for mensagem_usuario in bloco["mensagens"]:
                                todas_as_conversas.append(mensagem_usuario)
                                todas_as_conversas.append(resposta_bloco)
                        else:
                            print(f"   Aviso: Bloco de conversa mal formatado em {caminho_arquivo}: {bloco}")
                else:
                    print(f"  Aviso: Arquivo JSON {caminho_arquivo} não contém a chave 'conversas' ou não é uma lista.")
        except FileNotFoundError:
            print(f"  ERRO: Arquivo de conversas não encontrado: {caminho_arquivo}")
        except json.JSONDecodeError:
            print(f"  ERRO: Formato JSON inválido em: {caminho_arquivo}")
        except Exception as e:
            print(f"  ERRO ao processar {caminho_arquivo}: {e}")
    
    return todas_as_conversas

def treinar_robo(robo_instance, conversas):
    if not robo_instance:
        print("ERRO: Instância do robô não fornecida para treinamento.")
        return False
    
    if not conversas:
        print("Nenhuma conversa carregada. Treinamento não realizado.")
        return False
    
    print(f"\nIniciando treinamento com {len(conversas)//2} pares de pergunta/resposta...")
    trainer = ListTrainer(robo_instance)
    trainer.train(conversas)
    print("Treinamento concluído com sucesso.")
    return True

def main():
    print("=== TREINAMENTO DO CHATBOT ENEM ===")
    
    sucesso_init, robo = inicializar_robo()
    if not sucesso_init:
        print("Falha ao inicializar o robô. Treinamento cancelado.")
        return
    
    conversas = carregar_conversas_json(ARQUIVOS_JSON_CONVERSAS)
    
    sucesso_treino = treinar_robo(robo, conversas)
    
    if sucesso_treino:
        print("\nTreinamento concluído com sucesso! O chatbot está pronto para ser usado.")
        print("Execute o serviço.py para iniciar o backend da aplicação.")
    else:
        print("\nO treinamento não foi concluído devido a erros.")

if __name__ == "__main__":
    main()