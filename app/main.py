from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.ai_hf_service import CodeExplainerAI
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Code Explainer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

static_dir = os.path.join(project_root, "static")
templates_dir = os.path.join(project_root, "templates")

templates = Jinja2Templates(directory=templates_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

ai_service = CodeExplainerAI()


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/explain")
async def explain_code(request: Request):
    try:
        data = await request.json()
        code = data.get("code", "").strip()
        language = data.get("language", "auto")

        if not code:
            raise HTTPException(status_code=400, detail="Введите код для анализа")

        logger.info(f"Анализируем код на {language}")

        explanation = await ai_service.explain_code(code, language)

        return {
            "success": True,
            "explanation": explanation,
            "language": language
        }

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/health")
async def health_check():
    return {"status": "работает", "service": "Анализатор кода"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
