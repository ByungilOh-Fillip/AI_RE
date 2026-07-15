# AI_RE Backend

FastAPI modular-monolith foundation for the C PC. The same application runs locally in `AI_MODE=mock` during development and later runs on the C PC with an AIService adapter selected by configuration.

## Local mock run

```powershell
Copy-Item .env.example .env
uv sync --dev
uv run alembic upgrade head
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Check `http://127.0.0.1:8000/health`. A phone on the same LAN uses the development PC's LAN address instead of `127.0.0.1`.

Generate separate local-only GameClient and WebClient bearer tokens before protected Mock API work:

```powershell
[Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

Place different generated values in `DEV_GAME_DEVICE_TOKEN` and `DEV_WEB_DEVICE_TOKEN` in the untracked `.env` file. M01 resolves the local Profile, Device, and Device role from these tokens. M02 replaces this development authenticator with pairing-issued tokens and hash-backed persistence.

The MVP database is `Backend/aire.db`, created by Alembic rather than application
startup code. Apply and roll back the schema with:

```powershell
uv run alembic upgrade head
uv run alembic downgrade base
```

SQLite runs with foreign keys, WAL and a five-second busy timeout. The Backend
must use one worker during this MVP. PostgreSQL becomes a separate promotion and
data-migration task if pgvector or higher write concurrency becomes required.

`POST /api/v1/chat` requires the role-appropriate development bearer token.
Offline requests use the WebClient token and RealWorld `observed_at` plus an IANA
timezone. Set `MOCK_AI_SCENARIO` to `normal`, `timeout`, `unavailable`, or
`invalid_output` to reproduce normalized AI paths. Request bodies and
Authorization values are intentionally omitted from structured logs.
