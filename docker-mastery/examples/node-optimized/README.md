# node-optimized · Best-Practices Dockerfile

A small Node HTTP server that shows the optimization + hardening checklist from
[Module 08](../../docs/08-optimization.md) and [Module 10](../../docs/10-security-advanced.md):

- **Alpine base** — tiny footprint.
- **Dependency-first ordering** — `COPY package*.json` + `npm install` before `COPY . .`,
  so code edits don't bust the dependency cache.
- **`.dockerignore`** — keeps `node_modules`, `.git`, and `.env` out of the image.
- **Non-root `USER`** — the process runs as `app`, not root.
- **`HEALTHCHECK`** — Docker knows when the app is actually alive.
- **Exec-form `CMD`** — clean shutdown on `docker stop`.

## Run

```bash
docker build -t node-optimized .
docker run -d -p 3000:3000 --name node-app node-optimized
curl localhost:3000
curl localhost:3000/health
docker inspect --format '{{.State.Health.Status}}' node-app
docker rm -f node-app
```
