# GameClient: start_game(), guess(), delete_game()
import httpx

from .config import settings


class GameClient:
    """Wraps all HTTP calls to the Game Host into simple Python methods.
    """

    def __init__(self):
        # The API key goes into every request automatically via default_headers.
        # We set it once here so every method gets it for free.
        self._client = httpx.Client(
            base_url=settings.host_url.rstrip("/"),
            headers={"X-API-Key": settings.api_key},
            timeout=10.0,
        )

    def start_game(self) -> str:
        """POST /games → returns the game_id string."""
        resp = self._client.post("/games")
        resp.raise_for_status()   # raises an exception if status >= 400
        return resp.json()["game_id"]

    def guess(self, game_id: str, number: int) -> str:
        """POST /games/{id}/guess → returns 'lower', 'higher', or 'correct'."""
        resp = self._client.post(f"/games/{game_id}/guess", json={"guess": number})
        resp.raise_for_status()
        return resp.json()["result"]

    def delete_game(self, game_id: str) -> None:
        """DELETE /games/{id} — clean up after the game ends."""
        resp = self._client.delete(f"/games/{game_id}")
        resp.raise_for_status()

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()
