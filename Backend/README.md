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

Place generated values in `DEV_GAME_DEVICE_TOKEN` and `DEVICE_CREDENTIAL_PEPPER` in the untracked `.env` file. The Game token is accepted only by `POST /api/v1/devices/register-game`; the pepper protects persisted Device Token and Pairing Code hashes. Pairing-issued raw credentials are returned by their creation response and are never stored or logged.

The MVP database is `Backend/aire.db`, created by Alembic rather than application
startup code. Apply and roll back the schema with:

```powershell
uv run alembic upgrade head
uv run alembic downgrade base
```

SQLite runs with foreign keys, WAL and a five-second busy timeout. The Backend
must use one worker during this MVP. PostgreSQL becomes a separate promotion and
data-migration task if pgvector or higher write concurrency becomes required.

`POST /api/v1/chat` requires a registered GameClient or paired WebClient bearer token.
Offline requests use the WebClient token and RealWorld `observed_at` plus an IANA
timezone. Set `MOCK_AI_SCENARIO` to `normal`, `timeout`, `unavailable`, or
`invalid_output` to reproduce normalized AI paths. Request bodies and
Authorization values are intentionally omitted from structured logs.
