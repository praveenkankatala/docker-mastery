# three-tier-app · Networks + Volumes in the Real World

A production-shaped topology: **frontend → backend → database**, wired so the
public frontend physically cannot reach the database.

## The security model

| Service  | Networks                    | Published? | Why |
|----------|-----------------------------|-----------|-----|
| frontend | `frontend-net`              | yes (8080) | Public entry point |
| backend  | `frontend-net`+`backend-net`| no        | Bridges the two tiers |
| database | `backend-net`               | no        | Private; a compromised frontend can't touch it |

Because `frontend` is not attached to `backend-net`, there is **no network path**
from it to `database`. That's the whole point.

## Volumes

- `db_data` — Postgres data survives `docker compose down` and container recreates.
- `static_files` — backend mounts it read-write to save uploads; frontend mounts it
  read-only to serve them. Files appear to the frontend the instant the backend writes.

> The database password is injected via a Compose **secret** (mounted at
> `/run/secrets/db_password`), not an environment variable — see
> [Module 10](../../docs/10-security-advanced.md).

## Run

```bash
docker compose up -d
docker compose ps
# Prove isolation: frontend cannot resolve/reach the database
docker compose exec frontend sh -c "wget -qO- http://database:5432 || echo 'blocked as expected'"
docker compose down          # add -v to also wipe the volumes (deletes data)
```
