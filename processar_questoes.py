import nltk
from nltk import word_tokenize, corpus
from nltk.corpus import floresta

from collections import Counter
from string import punctuation

import sqlite3
import os
import json
import re

ENEM_QUESTOES_JSON = "questoes/questoes.json"
CAMINHO_BD = "."
BD_ENEM = f"{CAMINHO_BD}/questoes.sqlite3"
PALAVRAS_CHAVE_POR_QUESTAO = 5  

CLASSES_GRAMATICAIS_INDESEJADAS = [
  "adv",
  "v-inf",
  "v-fin",
  "v-pcp",
  "v-ger",
  "num",
  "adj"      
]

MATERIAS_ENEM = [
  "matemática", "matematica", "português", "portugues",
  "história", "historia","geografia",  "biologia",
  "física", "fisica",  "química", "quimica", "linguagens", 
  "humanas", "natureza", "filosofia"
]


def inicializar():
    palavras_de_parada = set(corpus.stopwords.words("portuguese"))
    floresta.tagged_words()

    classificacoes = {}
    for (palavra, classificacao) in floresta.tagged_words():
        classificacoes[palavra.lower()] = classificacao
    return palavras_de_parada, classificacoes

def ler_questoes_do_json(caminho_arquivo_json):
    sucesso, dados_questoes = False, None

    try:
      with open(caminho_arquivo_json, "r", encoding="utf-8") as arquivo:
          dados_questoes = json.load(arquivo)
          arquivo.close()
      sucesso = True
    except Exception as x:
        print(f"ERRO: Arquivo JSON não encontrado:{x}")
    return sucesso, dados_questoes


def eliminar_palavras_de_parada(tokens, palavras_de_parada):
  tokens_filtrados = []
  for token in tokens:
    if token not in palavras_de_parada:
      tokens_filtrados.append(token)
  return tokens_filtrados

def eliminar_pontuacoes(tokens):
  tokens_filtrados = []
  for token in tokens:
    if token not in punctuation:
      tokens_filtrados.append(token)
  return tokens_filtrados

def eliminar_classes_gramaticais(tokens, classificacoes_palavras):
    tokens_filtrados = []
    if not classificacoes_palavras:
        return tokens

    for token in tokens:
        classe = classificacoes_palavras.get(token.lower())
        if classe:
            if not any(classe_indesejada in classe for classe_indesejada in CLASSES_GRAMATICAIS_INDESEJADAS):
                tokens_filtrados.append(token)
        else:
            tokens_filtrados.append(token)
    return tokens_filtrados

def extrair_palavras_chave(texto, palavras_de_parada, classificacoes_palavras, num_chaves=5):
    if not texto:
        return []
    tokens = word_tokenize(texto.lower())
    tokens = eliminar_pontuacoes(tokens)
    tokens = eliminar_palavras_de_parada(tokens, palavras_de_parada)
    tokens = eliminar_classes_gramaticais(tokens, classificacoes_palavras)

    contagem = Counter(tokens)
    palavras_chave = [palavra for palavra, freq in contagem.most_common(num_chaves)]
    return palavras_chave


def iniciar_banco_enem():
    if os.path.exists(BD_ENEM):
        os.remove(BD_ENEM)

    conexao = sqlite3.connect(BD_ENEM)
    cursor = conexao.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questoes_enem (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        materia TEXT NOT NULL,
        ano INTEGER,
        numero_questao INTEGER,
        pergunta TEXT NOT NULL,
        alternativas TEXT,
        resposta_correta TEXT,
        explicacao TEXT
    )
    """)

    colunas_chaves = ", ".join([f"chave{i+1} TEXT" for i in range(PALAVRAS_CHAVE_POR_QUESTAO)])
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS chaves_enem (
        id_questao INTEGER NOT NULL,
        {colunas_chaves},
        FOREIGN KEY (id_questao) REFERENCES questoes_enem (id)
    )
    """)

    conexao.commit()
    conexao.close()

def gravar_questao_no_bd(conexao, questao_info, palavras_chave_extraidas):
   
    cursor = conexao.cursor()

    sql_insert_questao = """
    INSERT INTO questoes_enem (materia, ano, numero_questao, pergunta, alternativas, resposta_correta, explicacao)
    VALUES (:materia, :ano, :numero_questao, :pergunta, :alternativas, :resposta_correta, :explicacao)
    """
    cursor.execute(sql_insert_questao, questao_info)
    id_questao_inserida = cursor.lastrowid

    chaves_para_sql = palavras_chave_extraidas[:PALAVRAS_CHAVE_POR_QUESTAO]
    while len(chaves_para_sql) < PALAVRAS_CHAVE_POR_QUESTAO:
        chaves_para_sql.append(None)

    colunas_chaves_nomes = ", ".join([f"chave{i+1}" for i in range(PALAVRAS_CHAVE_POR_QUESTAO)])
    placeholders_chaves = ", ".join(["?"] * PALAVRAS_CHAVE_POR_QUESTAO)

    sql_insert_chaves = f"""
    INSERT INTO chaves_enem (id_questao, {colunas_chaves_nomes})
    VALUES (?, {placeholders_chaves})
    """
    cursor.execute(sql_insert_chaves, (id_questao_inserida, *chaves_para_sql))

def get_questoes_do_bd(materia_filtro=None, como_linhas=False):
    conexao = sqlite3.connect(BD_ENEM)
    if como_linhas:
        conexao.row_factory = sqlite3.Row

    cursor = conexao.cursor()

    query_base = """
    SELECT q.id, q.materia, q.ano, q.numero_questao, q.pergunta, q.alternativas, q.resposta_correta, q.explicacao,
           c.chave1, c.chave2, c.chave3, c.chave4, c.chave5 
           -- Adapte o número de chaves se PALAVRAS_CHAVE_POR_QUESTAO for diferente de 5
    FROM questoes_enem q
    LEFT JOIN chaves_enem c ON q.id = c.id_questao
    """

    params = ()
    if materia_filtro:
        query_base += " WHERE q.materia = ?"
        params = (materia_filtro,)

    cursor.execute(query_base, params)
    questoes_encontradas = cursor.fetchall()
    conexao.close()
    return questoes_encontradas


def identificar_materia(texto):
    if not texto:
        return None
        
    texto_lower = texto.lower()
    
    for materia in MATERIAS_ENEM:
        if materia == texto_lower or f"{materia} " in texto_lower or f" {materia}" in texto_lower:
            if materia in ["matemática", "matematica", "matemática e suas tecnologias"]:
                return "Matemática"
            elif materia in ["português", "portugues", "inglês", "ingles", "espanhol", "artes", "educação física", "educacao fisica", "linguagens", "linguagens e suas tecnologias"]:
                return "Linguagens"
            elif materia in ["história", "historia", "geografia", "filosofia", "sociologia", "ciências humanas", "ciencias humanas"]:
                return "Ciências Humanas"
            elif materia in ["física", "fisica", "química", "quimica", "biologia", "ciências da natureza", "ciencias da natureza"]:
                return "Ciências da Natureza"
    
   
    return None

def extrair_termos_pesquisa(texto, materia_identificada):
   
    if not materia_identificada:
        texto_processado = texto
    else:
       
        materia_regex = '|'.join(re.escape(mat) for mat in MATERIAS_ENEM)
        texto_processado = re.sub(materia_regex, '', texto.lower(), flags=re.IGNORECASE)
    
    texto_processado = re.sub(r'[^\w\s]', ' ', texto_processado)
    texto_processado = re.sub(r'\s+', ' ', texto_processado).strip()
    
    return texto_processado

def formatar_questao(questao):
    texto = f"\n📝 Questão {questao['numero_questao']} de {questao['materia']} ({questao['ano']})\n\n"
    texto += f"{questao['pergunta']}\n\n"
    
    alternativas = sorted(questao['alternativas'].items())
    for letra, conteudo in alternativas:
        texto += f"{letra}) {conteudo}\n"
    
    return texto

def formatar_resposta(questao):
    texto = f"\n✅ A resposta correta é a alternativa {questao['resposta_correta']}.\n\n"
    texto += f"📚 Explicação: {questao['explicacao']}\n"
    
    return texto

def pesquisar_questoes(materia=None, termos=None, limite=10):
    try:
        conexao = sqlite3.connect(BD_ENEM)
        conexao.row_factory = sqlite3.Row
        cursor = conexao.cursor()
        
        query = """
        SELECT DISTINCT q.id, q.materia, q.ano, q.numero_questao, q.pergunta, q.alternativas, q.resposta_correta, q.explicacao
        FROM questoes_enem q
        LEFT JOIN chaves_enem c ON q.id = c.id_questao
        WHERE 1=1
        """

        params = []
        
        if materia and materia.strip():
            materia_normalizada = normalizar_materia(materia.strip())
            if materia_normalizada:
                if materia_normalizada in ["Matemática", "Linguagens", "Ciências Humanas", "Ciências da Natureza"]:
                    query += " AND q.materia = ?"
                    params.append(materia_normalizada)
                else:
                    query += " AND q.materia LIKE ?"
                    params.append(f"%{materia_normalizada}%")
        
        if termos and termos.strip():
            termos_lista = termos.split()
            if termos_lista:
                query += " AND ("
                termo_conditions = []
                
                for termo in termos_lista:
                    termo = termo.strip()
                    if termo and len(termo) > 2:  
                        termo_condition = "(q.pergunta LIKE ? OR q.explicacao LIKE ? OR c.chave1 LIKE ? OR c.chave2 LIKE ? OR c.chave3 LIKE ? OR c.chave4 LIKE ? OR c.chave5 LIKE ?)"
                        termo_conditions.append(termo_condition)
                        termo_busca = f"%{termo}%"
                        params.extend([termo_busca] * 7)  
                
                if termo_conditions:
                    query += " OR ".join(termo_conditions)
                else:
                    query = query[:-5]
                
                if termo_conditions:
                    query += ")"
        
        query += " ORDER BY q.materia, q.ano DESC LIMIT ?"
        params.append(limite)
        
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        
        questoes = []
        for row in resultados:
            questao = dict(row)
            questao['alternativas'] = json.loads(questao['alternativas'])
            questoes.append(questao)
        
        conexao.close()
        return questoes
    
    except Exception as e:
        print(f"Erro ao pesquisar questões: {e}")
        traceback.print_exc()
        return []

def normalizar_materia(materia_texto):
    if not materia_texto:
        return None
        
    materia_lower = materia_texto.lower()
    
    mapa_materias = {
        "Matemática": ["matematica", "matemática", "exatas", "algebra", "geometria", 
                      "trigonometria", "probabilidade", "estatistica"],
        
        "Linguagens": ["linguagens", "portugues", "português", "lingua", "língua", "linguas", "línguas", "literatura", 
                     "gramática", "gramatica", "interpretação", "interpretacao"],
        
        "Ciências Humanas": ["humanas", "historia", "história", "geografia", "sociologia", 
                          "filosofia", "politica", "política", "sociologia", "economia",
                           "filosofica", "histórica", "geografica", "ciencias humanas", "ciências humanas"],
        
        "Ciências da Natureza": ["natureza", "física", "fisica", "química", "quimica", "biologia", 
                             "ciencia", "ciência", "ciencias", "ciências",
                             "ciencias da natureza", "ciências da natureza"]
    }
    
    if "ciencias da natureza" in materia_lower or "ciências da natureza" in materia_lower:
        return "Ciências da Natureza"
    
    if "ciencias humanas" in materia_lower or "ciências humanas" in materia_lower:
        return "Ciências Humanas"
    
    for materia_padrao, variantes in mapa_materias.items():
        for variante in variantes:
            if variante in materia_lower:
                return materia_padrao
    
    return materia_texto

def analisar_pergunta_usuario(pergunta_usuario):
    if not pergunta_usuario:
        return None, ""
    
    materia = identificar_materia(pergunta_usuario)
    
    termos = extrair_termos_pesquisa(pergunta_usuario, materia)
    
    return materia, termos

if __name__ == "__main__":
    
    palavras_de_parada_globais, classificacoes_globais = inicializar()

    sucesso_leitura, dados_json = ler_questoes_do_json(ENEM_QUESTOES_JSON)

    iniciar_banco_enem()
    print(f"Banco de dados '{BD_ENEM}' iniciado/recriado.")

    print(f"Processando {len(dados_json.get('questoes', []))} questões do JSON...")
    conexao_db = sqlite3.connect(BD_ENEM) 

    for questao_obj in dados_json.get('questoes', []):
        info_questao_atual = {
            "materia": questao_obj.get("materia"),
            "ano": questao_obj.get("ano"),
            "numero_questao": questao_obj.get("numero"),
            "pergunta": questao_obj.get("pergunta"),
            "alternativas": json.dumps(questao_obj.get("alternativas", {})), 
            "resposta_correta": questao_obj.get("resposta_correta"),
            "explicacao": questao_obj.get("explicacao")
        }

        texto_para_chaves = f"{info_questao_atual['pergunta']} {info_questao_atual.get('explicacao', '')}"
        chaves = extrair_palavras_chave(
            texto_para_chaves,
            palavras_de_parada_globais,
            classificacoes_globais,
            PALAVRAS_CHAVE_POR_QUESTAO
        )

        gravar_questao_no_bd(conexao_db, info_questao_atual, chaves)

    conexao_db.commit() 
    conexao_db.close()
    print("Todas as questões foram processadas e gravadas no banco de dados.")

    