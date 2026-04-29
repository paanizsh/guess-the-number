"""
Game Host — entry point.

Starts a FastAPI application that exposes:
  GET  /health          Health check (no auth required)
  POST /games           Start a new game          
  POST /games/{id}/guess Submit a guess           
  DELETE /games/{id}    Clean up a finished game  

Interactive API docs are available at http://localhost:8000/docs
"""
from fastapi import FastAPI
import logging
from .routers.games import router as games_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Guess the Number — Game Host",
    description=(
        "Authenticated REST API for the 'Guess the Number' game. "
    ),
    version="1.0.0",
)


app.include_router(games_router)

@app.get("/health", tags=["health"])
def health() -> dict:
    """No auth required — used by Docker to check the service is alive."""
    return {"status": "ok", "service": "game-host"}
