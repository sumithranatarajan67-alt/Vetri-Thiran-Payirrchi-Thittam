from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routes import router


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="FitBuddy AI Fitness Plan Generator",
    description="AI-powered personalized workout planner",
    version="1.0.0"
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

app.include_router(router)


@app.on_event("startup")
def startup():

    init_db()


@app.get("/health")
def health():

    return {
        "status": "ok"
    }