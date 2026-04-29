# Pydantic schemas: GuessResult, GuessRequest, GuessResponse, Token, UserCreate
from enum import Enum

from pydantic import BaseModel, Field


class GuessResult(str, Enum):
    """The only three possible answers the host can give."""
    LOWER   = "lower"    # your guess is too high, try lower
    HIGHER  = "higher"   # your guess is too low, try higher
    CORRECT = "correct"


class GameCreatedResponse(BaseModel):
    """What the host returns when you start a new game."""
    game_id: str
    message: str = "Game started. Make your first guess!"


class GuessRequest(BaseModel):
    """What the player sends when making a guess."""
    guess: int = Field(..., ge=1, le=10_000, description="Your guess must be between 1 and 10,000.")


class GuessResponse(BaseModel):
    """What the host returns after each guess."""
    game_id: str
    guess: int
    result: GuessResult
    attempts: int


class GameDeletedResponse(BaseModel):
    message: str