from nltk import word_tokenize, corpus
from nltk.corpus import floresta

TEXTO = "a verdadeira generosidade para com o futuro consiste em dar tudo ao presente" # albert camus

palavras_de_parada = set(corpus.stopwords.words("portuguese"))
print(f"palavras de parada: {palavras_de_parada}")

tokens = word_tokenize(TEXTO.lower())
for token in tokens:
    print(token)

tokens_filtrados = []
for token in tokens:
    if token not in palavras_de_parada:
        tokens_filtrados.append(token)
print(tokens_filtrados)

classificacoes = {}
for (palavra, classificacao) in floresta.tagged_words():
    classificacoes[palavra.lower()] = classificacao

if not "otimizar" in classificacoes.keys():
    print("otimizar não está classificada")
else:
    print(f"classe da palavra otimizar é: {classificacoes['otimizar']}")

for token in tokens:
    classificacao = classificacoes[token.lower()]
    print(f"{token} é um(a) {classificacao}")