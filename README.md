# ENEMExpert - Assistente de Estudos para o ENEM

Um assistente inteligente que ajuda estudantes a se prepararem para o ENEM, oferecendo respostas a perguntas sobre o exame e permitindo pesquisar questões por matéria e assunto.

## Características

- **Modo Conversacional**: Responde perguntas sobre o ENEM, datas, matérias e dicas de estudo
- **Busca de Questões**: Permite pesquisar questões por matéria e assunto
- **Interface Dupla**: Disponível como aplicação de linha de comando ou aplicação web

## Requisitos do Sistema

- Python 3.8 ou superior
- Banco de dados SQLite (incluído automaticamente)

## Configuração do Ambiente

### 1. Criação do Ambiente Virtual

```bash
python3 -m venv venv

source venv/bin/activate
```

### 2. Instalação das Dependências

```bash
pip install -r requirements.txt

python inicializar_nltk.py
```

## Preparação dos Dados

### 3. Processamento das Questões

```bash
python processar_questoes.py
```

Este script:

- Lê questões do arquivo `questoes/questoes.json`
- Extrai palavras-chave de cada questão
- Cria o banco de dados `questoes.sqlite3`

### 4. Treinamento do Chatbot

```bash
python treinamento.py
```

Este script:

- Carrega conversas de arquivos JSON em `./conversas/`
- Treina o modelo do chatbot e cria `chat.sqlite3`

## Execução do Sistema

### 5. Iniciar o Backend

```bash
python servico.py
```

O servidor ficará disponível em http://localhost:5000

### 6. Interface de Usuário

Você pode escolher entre dois métodos de interação:

#### Interface de Linha de Comando

```bash
source venv/bin/activate
python robo.py
```

#### Interface Web

```bash
source venv/bin/activate
python chat/chat.py
```

A interface web estará disponível em http://localhost:5001

## Uso do Sistema

### Modo Conversacional

- Faça perguntas sobre o ENEM, como datas, formato das provas, matérias, etc.
- Exemplo: "Quando será o próximo ENEM?"

### Modo Pesquisa de Questões

- Digite "pesquisar questões" para ativar o modo de pesquisa
- Especifique matéria e/ou assunto: "Matemática funções" ou "Ciências da Natureza física"
- Comandos disponíveis durante a pesquisa no front do terminal:
  - "próxima" - mostra a próxima questão
  - "anterior" - volta à questão anterior
  - "resposta" - mostra a resposta e explicação
  - "voltar" - retorna ao modo conversacional

#### Este projeto é para fins educacionais.