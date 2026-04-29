# Guess the Number

Two FastAPI microservices:
- **host** — picks a secret number [1–10 000], exposes a REST API with JWT auth
- **player** — auto-registers, finds the secret in ≤ 14 guesses via binary search

## Quick start

```bash
docker compose up --build
curl -X POST http://localhost:8001/play
```
