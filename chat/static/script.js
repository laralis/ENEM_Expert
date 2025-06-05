document.addEventListener("DOMContentLoaded", function () {
  const chatMessages = document.getElementById("chatMessages");
  const userInput = document.getElementById("userInput");
  const sendButton = document.getElementById("sendButton");
  const statusIndicator = document.getElementById("statusIndicator");
  const statusText = document.getElementById("statusText");
  const questionModal = new bootstrap.Modal(
    document.getElementById("questionModal")
  );
  const showAnswerButton = document.getElementById("showAnswerButton");
  let currentQuestion = null;

  fetch("/verificar_backend")
    .then((response) => response.json())
    .then((data) => {
      if (data.disponivel) {
        statusIndicator.className = "status-indicator status-online";
        statusText.textContent = "Serviço online";
      } else {
        statusIndicator.className = "status-indicator status-offline";
        statusText.textContent = "Serviço offline";
        addBotMessage(
          "O serviço backend não está disponível. Algumas funcionalidades podem não estar operando corretamente."
        );
      }
    })
    .catch((error) => {
      console.error("Erro ao verificar backend:", error);
      statusIndicator.className = "status-indicator status-offline";
      statusText.textContent = "Erro de conexão";
      addBotMessage(
        "Não foi possível verificar a conexão com o servidor. Por favor, tente mais tarde."
      );
    });

  function addUserMessage(text) {
    const messageDiv = document.createElement("div");
    messageDiv.className = "message user-message";
    messageDiv.innerHTML = `<p>${text}</p>`;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
  }

  function addBotMessage(text) {
    const messageDiv = document.createElement("div");
    messageDiv.className = "message bot-message";
    messageDiv.innerHTML = `<p>${text}</p>`;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
    return messageDiv;
  }

  function addQuestions(questions) {
    if (!questions || questions.length === 0) return;

    const questionsContainer = document.createElement("div");
    questionsContainer.className = "questions-container";

    questions.forEach((question) => {
      const card = document.createElement("div");
      card.className = "question-card";
      card.innerHTML = `
                        <h6>Questão ${question.numero} - ${question.materia} (${
        question.ano
      })</h6>
                        <p>${truncateText(question.pergunta, 150)}</p>
                    `;

      card.addEventListener("click", () => {
        showQuestionDetails(question);
      });

      questionsContainer.appendChild(card);
    });

    chatMessages.appendChild(questionsContainer);
    scrollToBottom();
  }

  function showQuestionDetails(question) {
    currentQuestion = question;

    const detailsContainer = document.getElementById("questionDetail");
    detailsContainer.innerHTML = `
                    <h5>Questão ${question.numero} de ${question.materia} (${
      question.ano
    })</h5>
                    <p>${question.pergunta}</p>
                    <div id="alternativas">
                        ${formatAlternatives(question.alternativas)}
                    </div>
                    <div id="explanation" style="display: none">
                        <hr>
                        <h6 class="text-success">Resposta correta: ${
                          question.resposta_correta
                        }</h6>
                        <p>${question.explicacao}</p>
                    </div>
                `;

    showAnswerButton.style.display = "block";
    questionModal.show();
  }

  function truncateText(text, maxLength) {
    if (!text) return "";
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
  }

  function formatAlternatives(alternatives) {
    if (!alternatives) return "";

    let html = '<div class="alternativas">';
    for (const [letter, text] of Object.entries(alternatives)) {
      html += `<div class="form-check">
                        <input class="form-check-input" type="radio" name="alternativa" id="alt${letter}" value="${letter}">
                        <label class="form-check-label" for="alt${letter}">${letter}) ${text}</label>
                    </div>`;
    }
    html += "</div>";

    return html;
  }

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function sendMessage() {
    const text = userInput.value.trim();
    if (text === "") return;

    addUserMessage(text);

    userInput.value = "";

    const typingIndicator = addBotMessage("...");

    fetch("/enviar_pergunta", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ pergunta: text }),
    })
      .then((response) => response.json())
      .then((data) => {
        typingIndicator.remove();

        addBotMessage(data.resposta);

        if (data.questoes && data.questoes.length > 0) {
          addQuestions(data.questoes);
        }
      })
      .catch((error) => {
        console.error("Erro ao enviar pergunta:", error);
        typingIndicator.remove();
        addBotMessage(
          "Ocorreu um erro ao processar sua pergunta. Por favor, tente novamente mais tarde."
        );
      });
  }

  sendButton.addEventListener("click", sendMessage);
  userInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      sendMessage();
    }
  });

  showAnswerButton.addEventListener("click", function () {
    document.getElementById("explanation").style.display = "block";
    this.style.display = "none";
  });
});
