# AI_RE WebApp

Framework-free Vite + strict TypeScript foundation for the B phone WebApp. It verifies connectivity to the mock Backend without committing the project to a UI framework before the Offline Chat task.

## Local run

```powershell
Copy-Item .env.example .env
npm.cmd install
npm.cmd run dev
```

Vite listens on the LAN and proxies `/health` and `/api` to the local Backend during development.
