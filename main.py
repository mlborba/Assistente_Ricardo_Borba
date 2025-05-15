# -*- coding: utf-8 -*-
import os
import google.generativeai as genai
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

# Carregar a chave da API da variável de ambiente
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("AVISO: A variável de ambiente GOOGLE_API_KEY não está configurada. O chatbot pode não funcionar.")
    # Para implantação na Vercel, esta variável DEVE ser configurada nas configurações do projeto.
else:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
    except Exception as e:
        print(f"Erro ao configurar a API Gemini: {e}")

app = FastAPI()

# Montar arquivos estáticos (CSS, JS, imagens)
app.mount("/static", StaticFiles(directory="/home/ubuntu/chatbot_project/static"), name="static")

# Configurar templates Jinja2 para servir o HTML
templates = Jinja2Templates(directory="/home/ubuntu/chatbot_project/templates")

# Configuração do modelo (do código original do usuário)
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = None
if GOOGLE_API_KEY: # Só inicializa o modelo se a API key estiver presente
    try:
        model = genai.GenerativeModel(
          model_name="gemini-1.5-flash",
          generation_config=generation_config,
          # safety_settings = Adjust safety settings (opcional)
        )
    except Exception as e:
        print(f"Erro ao inicializar o modelo Gemini: {e}")

class ChatMessage(BaseModel):
    message: str
    history: list = [] # Espera uma lista de dicts: [{"role": "user/model", "parts": [{"text": "..."}]}]

@app.post("/chat")
async def chat_endpoint(chat_message: ChatMessage):
    if not model:
        raise HTTPException(status_code=503, detail="Modelo Gemini não inicializado. Verifique a configuração da API_KEY.")

    user_input = chat_message.message
    # A API espera que o histórico seja uma lista de Content (objetos ou dicts)
    # O cliente envia history como [{"role": "user", "text": "Olá"}, {"role": "model", "text": "Oi!"}]
    # Precisamos converter para o formato que model.start_chat espera:
    # [{"role": "user", "parts": [{"text": "Olá"}]}, {"role": "model", "parts": [{"text": "Oi!"}]}]
    formatted_history = []
    for item in chat_message.history:
        if isinstance(item, dict) and "role" in item and "text" in item:
            formatted_history.append({"role": item["role"], "parts": [{"text": item["text"]}]})
        # Se o cliente já enviar no formato correto de "parts", podemos adicionar uma verificação aqui.

    try:
        # Inicia uma nova sessão de chat com o histórico fornecido
        chat_session = model.start_chat(history=formatted_history)
        response = chat_session.send_message(user_input)
        
        # O cliente é responsável por adicionar a mensagem do usuário e a resposta do bot ao seu histórico local.
        return {"response": response.text}
    except Exception as e:
        print(f"Ocorreu um erro durante a chamada para a API Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar mensagem: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Este bloco é para execução local. A Vercel usará o `app` diretamente.
if __name__ == "__main__":
    if not GOOGLE_API_KEY:
        print("Para executar localmente, configure a variável de ambiente GOOGLE_API_KEY.")
        print("Exemplo: export GOOGLE_API_KEY='sua_chave_aqui'")
    else:
        print("Servidor de desenvolvimento rodando em http://127.0.0.1:8000")
        print("Acesse a interface do chat em http://127.0.0.1:8000/")
    uvicorn.run(app, host="0.0.0.0", port=8000)

