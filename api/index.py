from fastapi import FastAPI
import os
import google.generativeai as genai
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import pathlib

# Carregar a chave da API da variável de ambiente
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

app = FastAPI()

# Configuração do modelo
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

# Configurar a API Gemini se a chave estiver disponível
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(
      model_name="gemini-1.5-flash",
      generation_config=generation_config,
    )
else:
    model = None

# Montar diretório de templates - verificando se existe
templates_dir = "templates"
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir, exist_ok=True)
    # Criar um template HTML básico se não existir
    with open(os.path.join(templates_dir, "index.html"), "w") as f:
        f.write("""
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Assistente Pessoal - Ricardo Borba</title>
    <style>
        body {
            font-family: sans-serif;
            margin: 0;
            background-color: #f4f4f9;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
            box-sizing: border-box;
        }
        #chat-container {
            width: 100%;
            max-width: 600px;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            height: 80vh;
        }
        #chat-header {
            background-color: #007bff;
            color: white;
            padding: 15px;
            text-align: center;
            font-size: 1.2em;
        }
        #chat-messages {
            flex-grow: 1;
            padding: 20px;
            overflow-y: auto;
            border-bottom: 1px solid #ddd;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 20px;
            line-height: 1.4;
            max-width: 80%;
        }
        .user-message {
            background-color: #007bff;
            color: white;
            align-self: flex-end;
            margin-left: auto;
        }
        .bot-message {
            background-color: #e9e9eb;
            color: #333;
            align-self: flex-start;
            margin-right: auto;
        }
        #input-area {
            display: flex;
            padding: 15px;
            border-top: 1px solid #ddd;
            background-color: #f8f9fa;
        }
        #user-input {
            flex-grow: 1;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 20px;
            margin-right: 10px;
            font-size: 1em;
        }
        #send-button {
            padding: 10px 20px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            font-size: 1em;
        }
        #send-button:hover {
            background-color: #0056b3;
        }
        .loading-indicator {
            text-align: center;
            padding: 10px;
            color: #777;
        }
    </style>
</head>
<body>
    <div id="chat-container">
        <div id="chat-header">Assistente Pessoal - Ricardo Borba</div>
        <div id="chat-messages"></div>
        <div id="input-area">
            <input type="text" id="user-input" placeholder="Digite sua mensagem...">
            <button id="send-button">Enviar</button>
        </div>
    </div>

    <script>
        const chatMessages = document.getElementById('chat-messages');
        const userInput = document.getElementById('user-input');
        const sendButton = document.getElementById('send-button');
        let chatHistory = [];

        function addMessage(sender, text) {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message');
            if (sender === 'user') {
                messageDiv.classList.add('user-message');
                messageDiv.textContent = `Você: ${text}`;
            } else {
                messageDiv.classList.add('bot-message');
                messageDiv.textContent = `Bot: ${text}`;
            }
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function showLoading(isLoading) {
            let loadingDiv = document.getElementById('loading-indicator');
            if (isLoading) {
                if (!loadingDiv) {
                    loadingDiv = document.createElement('div');
                    loadingDiv.id = 'loading-indicator';
                    loadingDiv.classList.add('loading-indicator');
                    loadingDiv.textContent = 'Bot está digitando...';
                    chatMessages.appendChild(loadingDiv);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            } else {
                if (loadingDiv) {
                    loadingDiv.remove();
                }
            }
        }

        async function sendMessage() {
            const messageText = userInput.value.trim();
            if (messageText === '') return;

            addMessage('user', messageText);
            chatHistory.push({ role: "user", text: messageText });
            userInput.value = '';
            showLoading(true);
            sendButton.disabled = true;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        message: messageText,
                        history: chatHistory.slice(0, -1)
                    }),
                });

                showLoading(false);
                sendButton.disabled = false;

                if (!response.ok) {
                    const errorData = await response.json();
                    addMessage('bot', `Erro: ${errorData.detail || response.statusText}`);
                    chatHistory.pop();
                    return;
                }

                const data = await response.json();
                addMessage('bot', data.response);
                chatHistory.push({ role: "model", text: data.response });

            } catch (error) {
                showLoading(false);
                sendButton.disabled = false;
                addMessage('bot', 'Erro ao conectar com o servidor. Tente novamente.');
                console.error('Fetch error:', error);
                chatHistory.pop();
            }
        }

        sendButton.addEventListener('click', sendMessage);
        userInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        });

        addMessage('bot', 'Olá! Como posso te ajudar hoje?');
    </script>
</body>
</html>
        """)

templates = Jinja2Templates(directory=templates_dir)

# Verificar e criar pasta static se não existir
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

# Montar arquivos estáticos apenas se a pasta existir
if os.path.exists(static_dir) and os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

class ChatMessage(BaseModel):
    message: str
    history: list = []

@app.post("/chat")
async def chat_endpoint(chat_message: ChatMessage):
    if not model:
        return JSONResponse(
            status_code=503,
            content={"detail": "Modelo Gemini não inicializado. Verifique a configuração da API_KEY."}
        )

    user_input = chat_message.message
    formatted_history = []
    for item in chat_message.history:
        if isinstance(item, dict) and "role" in item and "text" in item:
            formatted_history.append({"role": item["role"], "parts": [{"text": item["text"]}]})

    try:
        chat_session = model.start_chat(history=formatted_history)
        response = chat_session.send_message(user_input)
        return {"response": response.text}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Erro ao processar mensagem: {str(e)}"}
        )

@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
