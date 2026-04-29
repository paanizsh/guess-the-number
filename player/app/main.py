# Entry point 
import logging

from fastapi import FastAPI, HTTPException

from .binary_search import binary_search
from .game_client import GameClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# One shared client for the lifetime of the process.
# With API key auth there's no login step — the client is ready immediately.
client = GameClient()

app = FastAPI(
    title="Guess the Number — Player Service",
    description="Call POST /play to run a full game using binary search.",
    version="1.0.0",
)


@app.post("/play", tags=["game"])
def play() -> dict:
    """Play a full game from start to finish using binary search.
    Guaranteed to find the secret in at most 14 guesses.
    """
    # 1. Ask the host to start a new game
    try:
        game_id = client.start_game()
        logger.info("Game started: id=%s", game_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not start game: {exc}")

    # 2. Wire binary_search to the host's guess endpoint.
    #    The algorithm only knows about ask() — no HTTP logic inside it.
    def ask(number: int) -> str:
        try:
            return client.guess(game_id, number)
        except Exception as exc:
            raise RuntimeError(f"Guess {number} failed: {exc}")

    try:
        secret, attempts, history = binary_search(ask=ask)
        logger.info("Game finished: secret=%s attempts=%s/14", secret, attempts)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # 3. Clean up the game on the host
    try:
        client.delete_game(game_id)
    except Exception as exc:
        logger.warning("Could not clean up game %s: %s", game_id, exc)

    return {
        "game_id": game_id,
        "secret_number": secret,
        "total_attempts": attempts,
        "max_possible_attempts": 14,
        "guess_history": history,
    }

@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "service": "player"}