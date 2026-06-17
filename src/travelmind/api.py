from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from travelmind.agent import TravelMindAgent
from travelmind.memory import TravelMemory
from travelmind.schemas import RecommendationRequest, RecommendationResponse, UserPreferences
from travelmind.tools.geocode import search_places


PACKAGE_DIR = Path(__file__).resolve().parent
STATIC_DIR = PACKAGE_DIR / "static"

app = FastAPI(title="TravelMind Agent", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory = TravelMemory()
agent = TravelMindAgent(memory=memory)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "travelmind-agent"}


@app.get("/api/preferences", response_model=UserPreferences)
def get_preferences() -> UserPreferences:
    return memory.get_preferences()


@app.post("/api/preferences", response_model=UserPreferences)
def save_preferences(preferences: UserPreferences) -> UserPreferences:
    memory.save_preferences(preferences)
    return preferences


@app.post("/api/recommend", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest) -> RecommendationResponse:
    return agent.recommend(request)


@app.get("/api/history")
def history() -> list[dict]:
    return memory.recent_history()


@app.get("/api/search")
def search(q: str, limit: int = 6) -> list[dict]:
    return search_places(q, limit=limit)


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
