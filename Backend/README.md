# AI_RE Backend

FastAPI modular-monolith foundation for the C PC. The same application runs locally in `AI_MODE=mock` during development and later runs on the C PC with an AIService adapter selected by configuration.

## Local mock run

```powershell
Copy-Item .env.example .env
uv sync --dev
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Check `http://127.0.0.1:8000/health`. A phone on the same LAN uses the development PC's LAN address instead of `127.0.0.1`.

Generate separate local-only GameClient and WebClient bearer tokens before protected Mock API work:

```powershell
[Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

Place different generated values in `DEV_GAME_DEVICE_TOKEN` and `DEV_WEB_DEVICE_TOKEN` in the untracked `.env` file. M01 resolves the local Profile, Device, and Device role from these tokens. M02 replaces this development authenticator with pairing-issued tokens and hash-backed persistence.

No LLM Runtime, model, or database is required for the health-only foundation. PostgreSQL, migrations, Chat/Event routes, and the concrete AIService are added by their owning tasks.
