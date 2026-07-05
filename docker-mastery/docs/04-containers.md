# 04 · Containers & Lifecycle

[◀ Images](./03-images.md) | [Back to README](../README.md) | [Next: Storage & Volumes ▶](./05-storage-volumes.md)

---

A **container** is a running instance of an image — a lightweight, isolated process that includes the app plus its runtime, libraries, and settings.

Unlike a VM that simulates *hardware*, a container simulates an *operating system* by sharing the host kernel and isolating itself with **namespaces** (privacy) and **cgroups** (limits). See [Module 01](./01-architecture.md).

---

## 1. The Container Lifecycle

```
        docker create              docker start            docker stop / kill
 IMAGE ───────────────▶ CREATED ───────────────▶ RUNNING ───────────────▶ STOPPED
                            ▲                        │  ▲                       │
                            └── docker run does ─────┘  │ docker pause          │ docker rm
                                both at once            ▼                       ▼
                                                     PAUSED                  DELETED
```

| State | Meaning |
|---|---|
| **Created** | Container exists but hasn't started |
| **Running** | Main process is executing |
| **Paused** | Process frozen in RAM |
| **Stopped** | Process killed; filesystem + logs still on disk |
| **Deleted** | Container and its writable layer gone |

---

## 2. The Writable Layer & Copy-on-Write

The image is read-only. A running container gets a thin **read-write layer** on top. Every file you create, log you write, or DB row you save lives there.

**Copy-on-Write (CoW):** if the app modifies a file that exists in the underlying image, Docker first copies it *up* into the writable layer, then edits the copy. The original image stays pristine.

> ⚠️ **The trap:** delete the container (`docker rm`) and the writable layer is destroyed — all data written inside is gone. To keep data, use **volumes** ([Module 05](./05-storage-volumes.md)).

---

## 3. Running Containers

```bash
# Foreground, interactive terminal
docker run -it ubuntu bash

# Detached (background), named, with port mapping
docker run -d --name web -p 8080:80 nginx

# One-off that cleans itself up on exit
docker run --rm alpine echo "hello"

# With env vars, resource limits, and a restart policy
docker run -d --name api \
  -e NODE_ENV=production \
  --memory=512m --cpus=1.0 \
  --restart=unless-stopped \
  -p 3000:3000 my-api:1.0
```

Key flags:

| Flag | Meaning |
|---|---|
| `-d` | Detached (background) |
| `-it` | Interactive + TTY (for shells) |
| `--name` | Assign a readable name |
| `-p H:C` | Publish host port H → container port C |
| `-e K=V` | Set an environment variable |
| `-v vol:/path` | Mount a volume |
| `--rm` | Auto-remove on exit |
| `--restart` | `no` / `on-failure` / `always` / `unless-stopped` |
| `--network` | Attach to a specific network |

---

## 4. Viewing & Inspecting

```bash
docker ps                     # running containers
docker ps -a                  # all (including stopped/exited)
docker logs web               # container's stdout/stderr
docker logs -f web            # follow logs live
docker logs --tail 100 web    # last 100 lines
docker inspect web            # full JSON: IP, mounts, env, config
docker stats                  # live CPU/mem/net usage (all containers)
docker top web                # processes running inside
docker port web               # published port mappings
```

---

## 5. Interacting With Running Containers

```bash
# Open a shell inside a running container (debugging)
docker exec -it web /bin/bash      # or /bin/sh if bash isn't installed

# Run a one-off command inside
docker exec web ls /etc/nginx

# Copy files in/out
docker cp ./config.conf web:/etc/nginx/conf.d/
docker cp web:/var/log/nginx/access.log ./

# Rename
docker rename web frontend
```

> `docker exec` "teleports" you into the container's namespaces. It's for debugging — don't treat containers as machines you SSH into and hand-configure. Rebuild the image instead (immutable infrastructure).

---

## 6. Stopping, Restarting, Removing

```bash
docker stop web        # graceful: SIGTERM, then SIGKILL after ~10s
docker kill web        # immediate: SIGKILL
docker restart web     # stop + start
docker start web       # start a stopped container
docker pause web       # freeze
docker unpause web

docker rm web          # remove a stopped container
docker rm -f web       # force-remove a running one
docker container prune # remove ALL stopped containers
```

**`stop` vs `kill`:** `stop` sends `SIGTERM` and gives the app a grace period to flush and shut down cleanly, then `SIGKILL`s if it hangs. `kill` skips straight to `SIGKILL`. Prefer `stop`.

---

## 7. Container Design Principles

- **One main process per container.** Web server *or* database — not a monolith running both.
- **Stateless where possible.** Store state in volumes or external services, not the writable layer.
- **Immutable infrastructure.** Don't patch a running container — build a new image and replace it.
- **Log to stdout/stderr.** Docker captures those (`docker logs`). Don't write logs to files inside the container.

---

## 8. Names vs IDs

Most commands accept either the container **name** (`web`) or **ID** (`4c01db0b339c`). For IDs, the first few unique characters are enough:

```bash
docker stop 4c0
```

---

## 🧪 Lab

See [labs/labs.md → Lab 4](../labs/labs.md#lab-4--container-lifecycle--exec). Run nginx detached, exec in, edit a file, watch it vanish after `rm`, then prove a volume fixes it.

---

## ⚠️ Common Pitfalls

- **Storing data in the container.** It dies with `docker rm`. Use volumes.
- **`docker kill` by default.** Skips graceful shutdown; can corrupt data mid-write. Use `stop`.
- **Treating containers like servers** you SSH into and configure by hand. Bake changes into the image.
- **Forgetting `-a` on `docker ps`.** Stopped containers are invisible without it — and they still hold names/ports.
- **Port already allocated errors.** Two containers can't publish to the same host port; change `-p`.

---

## ✅ Knowledge Check

1. What happens to files written inside a container when you `docker rm` it?
2. Difference between `docker stop` and `docker kill`?
3. What does `docker exec -it <c> bash` do?
4. Why should a container log to stdout instead of a file?

<details>
<summary>Answers</summary>

1. They're in the writable layer, which is destroyed — data is lost unless a volume was mounted.
2. `stop` = graceful SIGTERM then SIGKILL after a grace period; `kill` = immediate SIGKILL.
3. Opens an interactive shell inside the running container's namespaces for debugging.
4. Docker captures stdout/stderr so `docker logs` (and log drivers/aggregators) work; files inside the container are lost on removal and harder to collect.
</details>

---

[◀ Images](./03-images.md) | [Back to README](../README.md) | [Next: Storage & Volumes ▶](./05-storage-volumes.md)
