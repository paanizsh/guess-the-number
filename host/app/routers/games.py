import random
import uuid
from typing import Annotated
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import verify_api_key
from ..models import GameCreatedResponse, GameDeletedResponse, GuessRequest, GuessResponse, GuessResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/games", tags=["games"])

# In-memory storage: a plain dictionary that lives as long as the process does.
# Key   = game_id (a unique string)
# Value = { secret number, attempt count, whether the game is finished }
_games: dict[str, dict] = {}


@router.post("", response_model=GameCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_game(_: Annotated[None, Depends(verify_api_key)]) -> GameCreatedResponse:
    """Start a new game. The host picks a secret number and returns a game_id."""
    game_id = str(uuid.uuid4())   # uuid4 = random unique ID, e.g. "3f2a1b9c-..."
    _games[game_id] = {
        "secret": random.randint(1, 10_000),
        "attempts": 0,
        "finished": False,
    }
    logger.info("Game created: id=%s secret=%s", game_id, _games[game_id]["secret"])
    return GameCreatedResponse(game_id=game_id)


@router.post("/{game_id}/guess", response_model=GuessResponse)
def submit_guess(
    game_id: str,
    body: GuessRequest,
    _: Annotated[None, Depends(verify_api_key)],
) -> GuessResponse:
    """Submit a guess. Returns 'lower', 'higher', or 'correct'."""
    game = _games.get(game_id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found.")
    if game["finished"]:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Game already finished.")

    game["attempts"] += 1
    logger.info("Guess received: game=%s guess=%s attempt=%s", game_id, body.guess, game["attempts"])
    if body.guess < game["secret"]:
        result = GuessResult.HIGHER    # secret is higher than the guess
    elif body.guess > game["secret"]:
        result = GuessResult.LOWER     # secret is lower than the guess
    else:
        result = GuessResult.CORRECT
        game["finished"] = True
        logger.info("Game solved: id=%s secret=%s attempts=%s", game_id, game["secret"], game["attempts"])

    return GuessResponse(
        game_id=game_id,
        guess=body.guess,
        result=result,
        attempts=game["attempts"],
    )


@router.delete("/{game_id}", response_model=GameDeletedResponse)
def delete_game(
    game_id: str,
    _: Annotated[None, Depends(verify_api_key)],
) -> GameDeletedResponse:
    """Clean up a finished game from memory."""
    if game_id not in _games:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found.")
    del _games[game_id]
    logger.info("Game deleted: id=%s", game_id)
    return GameDeletedResponse(message=f"Game {game_id} deleted.")
