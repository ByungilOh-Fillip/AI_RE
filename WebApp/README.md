# AI_RE WebApp

Framework-free Vite + strict TypeScript foundation for the B phone WebApp. It verifies connectivity to the mock Backend without committing the project to a UI framework before the Offline Chat task.

## Local run

```powershell
Copy-Item .env.example .env
npm.cmd install
npm.cmd run dev
```

Vite listens on the LAN and proxies `/health` and `/api` to the local Backend during development.

For the M01 development-auth Chat slice, copy `.env.example` to the untracked
`.env` file and set `VITE_DEV_WEB_DEVICE_TOKEN` to the same local-only value as
Backend `DEV_WEB_DEVICE_TOKEN`. Vite variables are bundled into the development
client, so this mechanism must not be used for production credentials; M02
pairing replaces it with a device token issued at runtime.
