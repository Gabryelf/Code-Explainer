from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from services.ai_service import CodeExplainerAI
import os

app = FastAPI(title="Code Explainer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Для Render - пути относительно корня проекта
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

ai_service = CodeExplainerAI()

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/explain")
async def explain_code(request: Request):
    data = await request.json()
    code = data.get("code", "").strip()
    language = data.get("language", "auto")
    
    if not code:
        return {"success": False, "error": "Введите код для анализа"}
    
    explanation = await ai_service.explain_code(code, language)
    
    return {
        "success": True,
        "explanation": explanation,
        "language": language
    }

# Для локального запуска
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
