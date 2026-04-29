# Guess the Number

Two FastAPI microservices that play a number-guessing game over HTTP.
The **Host** picks a secret number in [1–10 000]; the **Player** finds it in at most **14 guesses** using binary search.

---

## Quick start

```bash
docker compose up --build
```

Then in a separate terminal:

```bash
# Let the player run a full automated game
curl -X POST http://localhost:8001/play
```

Or play manually against the host yourself — see [Manual play](#manual-play) below.

---

## Architecture

```
┌─────────────────────────┐      X-API-Key header       ┌─────────────────────────┐
│     Player  :8001        │ ──── POST /games ──────────▶ │      Host  :8000         │
│                          │ ── POST /games/{id}/guess ──▶ │                          │
│  binary_search.py        │ ◀── lower / higher / correct─ │  picks secret [1–10000]  │
│  game_client.py          │ ── DELETE /games/{id} ──────▶ │  validates API key       │
└─────────────────────────┘                               └─────────────────────────┘
           │                                                          │
           └──────────────── game-network (bridge) ──────────────────┘
```

Both services run in Docker on a shared private network.
The player reaches the host by container name (`http://game-host:8000`) — Docker handles the DNS.

---

## Project structure

```
guess-the-number/
├── docker-compose.yml
├── frontend/
│   └── index.html            # Single-file UI — calls POST /play and animates guess history
├── host/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py           # FastAPI app, router registration, health check
│       ├── config.py         # Settings loaded from environment variables
│       ├── auth.py           # verify_api_key — FastAPI Depends() function
│       ├── models.py         # Pydantic schemas (request and response shapes)
│       └── routers/
│           └── games.py      # POST /games  POST /games/{id}/guess  DELETE /games/{id}
└── player/
    ├── Dockerfile
    ├── requirements.txt
    ├── app/
    │   ├── main.py           # FastAPI app, POST /play route
    │   ├── config.py         # Settings (HOST_URL, API_KEY)
    │   ├── game_client.py    # HTTP wrapper around the host API
    │   └── binary_search.py  # Pure algorithm — completely decoupled from HTTP
    └── tests/
        └── test_binary_search.py  # Unit tests — no server needed
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

Interactive docs available at [http://localhost:8000/docs](http://localhost:8000/docs)

### Player — port 8001

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/play` | Run a full game using binary search |

Interactive docs available at [http://localhost:8001/docs](http://localhost:8001/docs)

---

## Manual play

```bash
# 1. Start a game
curl -X POST http://localhost:8000/games \
  -H "X-API-Key: secret-api-key"

# 2. Submit a guess (replace <game_id> with the id from step 1)
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

---

## Testing

The binary search algorithm is unit-tested in isolation — no Docker, no running server required.

```bash
python3 -m pytest tests/test_binary_search.py
```

The test file uses a `fake_ask` function instead of real HTTP calls. It mimics the host's behaviour in pure Python: return `"correct"` when the guess matches the secret, `"higher"` when the secret is above it, and `"lower"` when below. Because `binary_search.py` only depends on a callable, swapping the real HTTP client for this fake requires zero changes to the algorithm.

| Test | What it verifies |
|------|-----------------|
| `test_finds_correct_number` | Binary search finds a specific known secret (7342) |
| `test_always_within_14_guesses` | The ≤ 14 guarantee holds for boundary values (1, 100, 5000, 9999, 10000) |
| `test_last_history_item_is_correct` | The final entry in guess history always has `result == "correct"` |

The boundary values in the second test are deliberate — `1` and `10000` are where off-by-one bugs tend to appear.

---

## Design decisions

### Authentication — API Key

Both services are operated by the same person and communicate over a private Docker network. In this context a shared API key passed as `X-API-Key` is the appropriate choice: it is simple, has zero dependencies, and keeps the focus on the game logic rather than auth infrastructure.

The conscious trade-off: API key auth provides no per-user identity and no token expiry. The natural next step would be JWT — each player would register, receive a signed token with an expiry, and the host would verify the signature without any database lookup. This would be the right upgrade if multiple independent players needed to interact with the same host, or if the host were exposed beyond a private network.

### Algorithm — Binary Search

The number range is fixed at [1–10 000] and the distribution is unknown. Binary search makes no assumptions and guarantees ≤ ⌈log₂(10 000)⌉ = **14 guesses** in all cases.

Interpolation search would be faster on uniformly distributed data (O(log log n) average) but degrades to O(n) if the distribution is skewed — a risk not worth taking when we cannot verify the host's behaviour. Exponential search solves a different problem (unknown upper bound) and adds complexity with no benefit here.

### Decoupled algorithm

`binary_search.py` takes an `ask(n)` callable and knows nothing about HTTP. This means it can be unit-tested without spinning up any server, and could be reused against any backend by swapping the `ask` function.

### In-memory storage

Games are stored in a plain Python dict. The trade-off: state is lost on restart and cannot be shared across multiple instances. Production alternative: Redis with TTL for automatic cleanup and horizontal scaling support.

---

## Azure deployment

Both services are deployed on **Azure Container Apps** — a serverless container platform built on Kubernetes that requires no infrastructure management.

### Architecture on Azure

```
Browser / curl
      │
      ▼
game-player  (external ingress — public HTTPS URL)
      │  https://game-host.internal.[env].azurecontainerapps.io
      ▼
game-host    (internal ingress — not reachable from the internet)
```

### Services used

| Service | Purpose |
|---|---|
| **Azure Container Registry** | Stores Docker images (`game-host`, `game-player`) |
| **Container Apps Environment** | Shared private network — both apps discover each other by name |
| **Container Apps** | Serverless runtime for each microservice — scales to zero when idle |

### Why Container Apps over the alternatives

**ACI (Container Instances)** — no service discovery between containers, no HTTPS out of the box. Good for a single container, awkward for two services that communicate.

**AKS (Kubernetes Service)** — full Kubernetes control but requires managing a cluster. Overkill for two microservices.

**Container Apps** — sits between the two. Kubernetes under the hood, but fully managed. Built-in service discovery, automatic HTTPS, scale to zero, and per-service ingress control (internal vs external) made it the right fit here.

### Deploy from scratch

**Prerequisites:** Azure CLI, Docker Desktop, an Azure subscription.

```bash
# 1. Create infrastructure
az group create --name guess-the-number-rg --location eastus
az acr create --resource-group guess-the-number-rg --name gtnregistry --sku Basic --admin-enabled true
az extension add --name containerapp --upgrade
az containerapp env create --name guess-env --resource-group guess-the-number-rg --location eastus

# 2. Build and push images (cross-compile for Azure's amd64 runtime)
docker build --platform linux/amd64 -t gtnregistry.azurecr.io/game-host:latest ./host
docker build --platform linux/amd64 -t gtnregistry.azurecr.io/game-player:latest ./player
az acr login --name gtnregistry
docker push gtnregistry.azurecr.io/game-host:latest
docker push gtnregistry.azurecr.io/game-player:latest

# 3. Deploy host (internal — no public URL)
az containerapp create --name game-host --resource-group guess-the-number-rg \
  --environment guess-env --image gtnregistry.azurecr.io/game-host:latest \
  --registry-server gtnregistry.azurecr.io --target-port 8000 \
  --ingress internal --env-vars API_KEY=secret-api-key --min-replicas 1

# 4. Get host's internal address
HOST_FQDN=$(az containerapp show --name game-host --resource-group guess-the-number-rg \
  --query properties.configuration.ingress.fqdn -o tsv)

# 5. Deploy player (external — public HTTPS URL)
az containerapp create --name game-player --resource-group guess-the-number-rg \
  --environment guess-env --image gtnregistry.azurecr.io/game-player:latest \
  --registry-server gtnregistry.azurecr.io --target-port 8001 \
  --ingress external --env-vars API_KEY=secret-api-key HOST_URL=https://$HOST_FQDN \
  --min-replicas 1

# 6. Get public URL and test
PLAYER_URL=$(az containerapp show --name game-player --resource-group guess-the-number-rg \
  --query properties.configuration.ingress.fqdn -o tsv)
curl -X POST https://$PLAYER_URL/play
```


## What's next

- **JWT authentication** — per-user identity, signed tokens, bcrypt password hashing, token expiry
- **Redis** — replace the in-memory dict for persistence and multi-instance support
- **Key Vault** — store `API_KEY` as a secret instead of a plain environment variable
- **CI/CD** — GitHub Actions to rebuild and redeploy on every push to `main`