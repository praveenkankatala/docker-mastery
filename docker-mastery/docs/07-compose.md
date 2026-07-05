# 07 · Docker Compose

[◀ Networking](./06-networking.md) | [Back to README](../README.md) | [Next: Optimization ▶](./08-optimization.md)

---

**Docker Compose** defines and runs multi-container applications from a single YAML file. Instead of a dozen `docker run` commands with flags for networks, ports, volumes, and env vars, you declare the whole stack once.

> If a Dockerfile is the recipe for one dish, Compose is the coordinator making sure the burger, fries, and drink all arrive together, correctly wired.

> **Command note:** modern Compose (v2) is a Docker plugin invoked as `docker compose` (space). The old standalone binary was `docker-compose` (hyphen). Prefer the space form.

---

## 1. Why Compose

A realistic app is several processes: frontend, backend API, database, cache. Wiring those by hand with `docker run` is tedious and error-prone. Compose puts networks, volumes, env, ports, and dependencies in one versioned file.

---

## 2. The `compose.yaml` File

The modern filename is `compose.yaml` (`docker-compose.yml` still works). The top-level `version:` key is now **obsolete** and can be omitted.

```yaml
services:
  web:
    build: .                    # build image from local Dockerfile
    ports:
      - "8000:5000"             # host:container
    volumes:
      - .:/code                 # bind-mount source for live reload
    environment:
      - FLASK_ENV=development
    depends_on:
      - redis                   # start redis first

  redis:
    image: "redis:alpine"       # pull a prebuilt image
```

Top-level keys:

| Key | Purpose |
|---|---|
| `services` | Each entry is a container |
| `networks` | Custom networks (auto-created if omitted) |
| `volumes` | Named volumes for persistence |

Common service keys: `image`, `build`, `ports`, `volumes`, `environment`, `env_file`, `depends_on`, `networks`, `restart`, `command`, `healthcheck`, `deploy`.

---

## 3. What Compose Does For You

**Automatic networking** — `docker compose up` creates a default network for the project and joins every service to it. Services reach each other by **service name** as hostname (the `web` app connects to `redis:6379`). No manual `docker network create`.

**Volume management** — declared named volumes persist across `up`/`down` cycles (unless you pass `-v`).

**Selective recreation** — change one service and re-run `up`; Compose only recreates what changed, leaving the rest running.

---

## 4. Essential Commands

Run these from the directory containing the compose file.

```bash
docker compose up            # build (if needed), create, start — foreground
docker compose up -d         # detached (background)
docker compose up --build    # force rebuild images first
docker compose down          # stop + remove containers & network
docker compose down -v       # ...also remove named volumes (deletes data!)

docker compose ps            # status of this project's services
docker compose logs -f       # follow combined logs from all services
docker compose logs -f web   # just one service
docker compose exec db psql  # run a command inside a service
docker compose build         # build images only
docker compose restart web   # restart one service
docker compose up --scale web=3   # run 3 replicas of "web"
```

---

## 5. `depends_on` — Order vs. Readiness

`depends_on` controls **start order**, but by default only waits for the container to **start**, not for the app inside to be **ready**. A Postgres container can be "up" while the DB engine is still initializing.

For true readiness, combine `depends_on` with a **healthcheck**:

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  web:
    build: .
    depends_on:
      db:
        condition: service_healthy   # wait until db passes its healthcheck
```

Now `web` won't start until `db` actually accepts connections.

---

## 6. Environment & Secrets

Keep secrets out of the compose file — use an `.env` file (gitignored) or `env_file`:

```yaml
services:
  db:
    image: postgres:16
    env_file:
      - .env            # POSTGRES_PASSWORD=... lives here, not in git
```

Variable substitution also works: `POSTGRES_PASSWORD: ${DB_PASSWORD}` reads from your shell/`.env`.

---

## 7. Compose vs. Raw Docker CLI

| | `docker run` | Docker Compose |
|---|---|---|
| Scope | One container | Whole multi-container stack |
| Defined by | CLI flags | YAML file (version-controlled) |
| Networking | Manual | Automatic |
| Reproducible | Hard | `git clone && docker compose up` |
| Scaling | Manual | `--scale web=3` |

---

## 🧪 Lab

See [labs/labs.md → Lab 7](../labs/labs.md#lab-7--multi-container-with-compose). Bring up the [`flask-redis`](../examples/flask-redis) example, watch the two services talk over the auto-created network, then tear it down.

Try it now:

```bash
cd examples/flask-redis
docker compose up -d
curl localhost:8000        # hit counter increments via Redis
docker compose down
```

---

## ⚠️ Common Pitfalls

- **Relying on `depends_on` for readiness.** It only waits for *start*. Add healthchecks with `condition: service_healthy`.
- **`docker compose down -v` by reflex.** The `-v` wipes named volumes — you lose your database.
- **Committing secrets in the compose file.** Use `.env` / `env_file` and gitignore them.
- **Mixing `docker-compose` (v1) and `docker compose` (v2)** habits — stick to v2.
- **Editing a running container by hand.** Change the compose file / image and re-`up`; Compose recreates cleanly.

---

## ✅ Knowledge Check

1. How do services in a Compose file address each other?
2. What does `depends_on` guarantee — and what does it *not*?
3. What's the difference between `docker compose down` and `docker compose down -v`?
4. Where should database passwords go instead of the compose file?

<details>
<summary>Answers</summary>

1. By service name as the hostname, over the auto-created project network.
2. It guarantees start *order*; it does **not** guarantee the app inside is ready to serve. Use a healthcheck + `condition: service_healthy`.
3. `down` removes containers + network; `down -v` also deletes named volumes (and their data).
4. In a gitignored `.env` / `env_file`, referenced via `env_file:` or `${VAR}` substitution.
</details>

---

[◀ Networking](./06-networking.md) | [Back to README](../README.md) | [Next: Optimization ▶](./08-optimization.md)
