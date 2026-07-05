# flask-redis · Compose Example

A minimal two-service stack: a Flask web app that counts page views in Redis.
Demonstrates **automatic Compose networking** (the app reaches Redis by the
service name `redis`), `depends_on` with a **healthcheck**, and cache-friendly
Dockerfile ordering.

## Run

```bash
docker compose up -d
curl localhost:8000        # view count increments each request
curl localhost:8000
docker compose down
```

## What to notice

- `app.py` connects to host `"redis"` — no IP. Compose's DNS resolves it.
- `web` waits for `redis` to pass its healthcheck before starting.
- The Dockerfile copies `requirements.txt` and installs **before** copying code,
  so dependency layers stay cached across code edits.
