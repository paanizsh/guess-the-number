# Guess the Number — API Key Auth

Two FastAPI microservices that play a number-guessing (between 1-10000) game over HTTP.
The **Host** picks a secret number; the **Player** finds it in at most **14 guesses** using binary search.

This is v — authentication is intentionally simple: a shared API key passed as an HTTP header.
See the [v2 branch](../guess-the-number) for the JWT upgrade.

---

## Quick start

```bash
docker compose up --build
```

Then in a separate terminal:

```bash
# Let the player run a full game automatically
curl -X POST http://localhost:8001/play
```

Or play manually against the host yourself (see [Manual play](#manual-play) below).

---

## Architecture

```
┌─────────────────────────┐        X-API-Key header        ┌─────────────────────────┐
│     Player  :8001       │ ─────── POST /games ─────────▶ │      Host  :8000        │
│                         │ ──── POST /games/{id}/guess ──▶│                         │
│  binary_search.py       │ ◀──── lower / higher / correct─│  picks secret [1–10000] │
│  game_client.py         │ ──── DELETE /games/{id} ──────▶│  validates API key      │
└─────────────────────────┘                                └─────────────────────────┘
           │                                                            │
           └─────────────────── game-network (bridge) ──────────────────┘
```

Both services run in Docker on a shared private network (`game-network`).
The player reaches the host by name (`http://game-host:8000`) — Docker handles the DNS.

---

## Project structure

```
guess-the-number-v1/
├── docker-compose.yml
├── host/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py           # FastAPI app, router registration
│       ├── config.py         # Settings from environment variables
│       ├── auth.py           # verify_api_key — FastAPI Depends() function
│       ├── models.py         # Pydantic schemas (request/response shapes)
│       └── routers/
│           └── games.py      # POST /games, POST /games/{id}/guess, DELETE /games/{id}
└── player/
    ├── Dockerfile
    ├── requirements.txt
    └── app/
        ├── main.py           # FastAPI app, POST /play route
        ├── config.py         # Settings (HOST_URL, API_KEY)
        ├── game_client.py    # HTTP wrapper around the host API
        └── binary_search.py  # Pure algorithm — no HTTP logic inside
```

---

## API reference

### Host — port 8000

All routes except `/health` require the header:
```
X-API-Key: <your-api-key>
```

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| `GET` | `/health` | Health check | No |
| `POST` | `/games` | Start a new game → returns `game_id` | Yes |
| `POST` | `/games/{id}/guess` | Submit a guess → `lower` / `higher` / `correct` | Yes |
| `DELETE` | `/games/{id}` | Clean up a finished game | Yes |

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Player — port 8001

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/play` | Run a full game using binary search |

Interactive docs: [http://localhost:8001/docs](http://localhost:8001/docs)

---

## Manual play

If you want to play the game yourself instead of letting the player do it:

```bash
# 1. Start a game
curl -X POST http://localhost:8000/games \
  -H "X-API-Key: secret-api-key"

# 2. Submit a guess (replace <game_id> with the value from step 1)
curl -X POST http://localhost:8000/games/<game_id>/guess \
  -H "X-API-Key: secret-api-key" \
  -H "Content-Type: application/json" \
  -d '{"guess": 5000}'

# 3. Clean up when done
curl -X DELETE http://localhost:8000/games/<game_id> \
  -H "X-API-Key: secret-api-key"
```

---

## Configuration

All configuration is passed via environment variables.
Defaults are provided so `docker compose up --build` works with zero setup.

| Variable | Service | Default | Description |
|----------|---------|---------|-------------|
| `API_KEY` | host + player | `secret-api-key` | Shared secret — must match on both sides |
| `HOST_URL` | player | `http://localhost:8000` | Overridden to `http://game-host:8000` inside Docker |

To use a custom key, create a `.env` file next to `docker-compose.yml`:

```
API_KEY=my-strong-secret
```

Docker Compose picks it up automatically.

> Never commit your `.env` file. Add it to `.gitignore`.

---

## Design decisions

**Why API key auth?**
A shared secret in a header is the simplest possible authentication scheme — zero dependencies, zero setup. Both services are operated by the same person, so per-user identity isn't needed. This is v1; [v2](../guess-the-number) evolves to JWT for per-user tokens and stateless verification.

**Why binary search?**
The range is known [1–10,000] and the number distribution is unknown. Binary search makes no assumptions and guarantees ≤ ⌈log₂(10,000)⌉ = **14 guesses** in all cases. Interpolation search can be faster on uniformly distributed data but degrades to O(n) if the distribution is skewed — a risk not worth taking.

**Why is `binary_search.py` decoupled from HTTP?**
The algorithm takes an `ask(n)` callable and knows nothing about HTTP. This means it can be unit-tested without spinning up any server, and could be reused against any backend by swapping the `ask` function.

**Why in-memory storage?**
A plain Python dict keeps the code simple and the focus on the game logic. The trade-off is that state is lost on restart and can't be shared across multiple instances. Production alternative: Redis with TTL.

---

## What's next (v2)

- Replace API key with **JWT authentication** — per-user identity, token expiry, bcrypt password hashing
- Add `POST /auth/register` and `POST /auth/login` to the host
- No changes needed to the game logic or binary search
