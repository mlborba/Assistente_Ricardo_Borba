from fastapi import FastAPI
import os
import google.generativeai as genai
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

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

# Montar diretório de templates
templates = Jinja2Templates(directory="templates")

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

# Montar arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
