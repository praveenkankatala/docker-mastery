# 02 · Dockerfile Deep Dive

[◀ Architecture](./01-architecture.md) | [Back to README](../README.md) | [Next: Images ▶](./03-images.md)

---

A **Dockerfile** is a plain text file (named `Dockerfile`, no extension) containing an ordered list of instructions. `docker build` executes them top to bottom to produce an image.

```
Dockerfile   =  the recipe
Image        =  the frozen meal (ready to cook)
Container    =  the hot meal on your plate (running)
```

---

## 1. Every Instruction Explained

### `FROM` — the base image (must be first)

Defines the image you build on top of. Always pin a specific tag.

```dockerfile
FROM python:3.12-slim
```

### `WORKDIR` — the working directory

Sets the current directory for every following instruction. Creates it if missing. Use this instead of `RUN cd`.

```dockerfile
WORKDIR /app
```

### `COPY` vs `ADD` — moving files in

- **`COPY`** — copies files/dirs from build context into the image. **Prefer this.**
- **`ADD`** — like `COPY` but *also* auto-extracts local tar archives and can fetch URLs. Its "magic" makes builds harder to reason about, so only use it when you specifically need extraction.

```dockerfile
COPY package.json package-lock.json ./
COPY . .
```

### `RUN` — execute commands at **build** time

Installs packages, compiles code, etc. Each `RUN` creates a new layer.

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
```

### `ENV` — environment variables (persist at **runtime**)

Available to the app inside the running container.

```dockerfile
ENV NODE_ENV=production
```

### `ARG` — build-time variables only

Available *during build*, gone once the image is built. Good for versions/flags.

```dockerfile
ARG APP_VERSION=1.0.0
```

> `ARG` values are visible in image history — **never put secrets in `ARG` or `ENV`.** Use BuildKit secrets (see [Module 10](./10-security-advanced.md)).

### `EXPOSE` — document the port

Documentation only — it does **not** publish the port. You still need `-p` at `docker run`.

```dockerfile
EXPOSE 8080
```

### `VOLUME` — declare a persistent mount point

Marks a directory whose data should live outside the container's writable layer.

```dockerfile
VOLUME ["/var/lib/data"]
```

### `USER` — drop root

Run the process as a non-root user (security best practice).

```dockerfile
RUN useradd -m appuser
USER appuser
```

### `HEALTHCHECK` — tell Docker how to test liveness

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8080/health || exit 1
```

### `ENTRYPOINT` vs `CMD` — what runs at **container start**

This trips everyone up. Both define the startup process; the difference is override behavior.

| | `CMD` | `ENTRYPOINT` |
|---|---|---|
| Purpose | Default command | Fixed executable the container *is* |
| Override at `docker run` | Easily replaced by args | Args are *appended* as parameters |
| Typical use | Apps you might override | Turn the container into a single tool |

```dockerfile
# CMD alone — override by passing a command
CMD ["python", "app.py"]

# ENTRYPOINT + CMD — ENTRYPOINT is the program, CMD is the default arg
ENTRYPOINT ["python"]
CMD ["app.py"]
# `docker run img script2.py` → runs `python script2.py`
```

> **Always use the exec form** (JSON array: `["python", "app.py"]`) not the shell form (`python app.py`). The exec form makes your process PID 1 directly, so it receives `SIGTERM` on `docker stop` and shuts down gracefully. The shell form wraps it in `/bin/sh -c`, which can swallow signals.

---

## 2. Instruction Timing Cheat Sheet

| Instruction | When | Purpose |
|---|---|---|
| `FROM` | Build | Sets the base OS/runtime |
| `ARG` | Build | Build-time variable |
| `RUN` | Build | Install / compile |
| `COPY` / `ADD` | Build | Bring code into the image |
| `ENV` | Runtime | App configuration |
| `EXPOSE` | Metadata | Document the port |
| `VOLUME` | Metadata | Declare persistent path |
| `USER` | Runtime | Which user the process runs as |
| `CMD` / `ENTRYPOINT` | Runtime | The command that starts the app |

---

## 3. Layering & Build Cache (the key to fast builds)

Each instruction creates a **layer**. Docker caches layers and reuses them if nothing above changed. The moment one layer's inputs change, that layer and **every layer after it** are rebuilt.

**Rule: order from least-frequently-changing to most-frequently-changing.**

```dockerfile
FROM node:18-alpine
WORKDIR /app

# 1. Dependency manifests change rarely → copy them first
COPY package.json package-lock.json ./
RUN npm ci                    # this expensive layer stays cached

# 2. Source code changes constantly → copy it last
COPY . .

CMD ["node", "index.js"]
```

If you copied all source *before* `npm ci`, every one-character code change would re-run the whole install. Ordering it this way means edits only invalidate the final cheap `COPY`.

---

## 4. `.dockerignore`

Like `.gitignore`, it keeps files out of the build context (what gets sent to the daemon and copied by `COPY . .`). Smaller context = faster builds + smaller, safer images.

```gitignore
.git
node_modules
dist
*.log
.env
Dockerfile
README.md
```

> Excluding `.env` here is a real security control — it prevents secrets from being baked into an image layer.

---

## 5. A Complete, Correct Example (Node.js)

```dockerfile
# syntax=docker/dockerfile:1

FROM node:18-alpine
# Working directory
WORKDIR /usr/src/app
# Dependencies first (cache-friendly)
COPY package*.json ./
RUN npm ci --omit=dev
# Application code
COPY . .
# Run as non-root
RUN addgroup -S app && adduser -S app -G app
USER app
# Document the port
EXPOSE 3000
# Liveness probe
HEALTHCHECK CMD wget -qO- http://localhost:3000/health || exit 1
# Start (exec form → clean signal handling)
CMD ["node", "index.js"]
```

Build and run:

```bash
docker build -t my-app:1.0 .
docker run -d -p 3000:3000 --name my-app my-app:1.0
```

---

## 🧪 Lab

See [labs/labs.md → Lab 2](../labs/labs.md#lab-2--write-and-build-a-dockerfile). You'll write a Dockerfile, build it, and prove the cache works by rebuilding after a code change.

---

## ⚠️ Common Pitfalls

- **`EXPOSE` ≠ publishing.** It's documentation; you still need `-p host:container` to reach the app.
- **Copying source before dependencies.** Kills the cache and slows every build.
- **Secrets in `ARG`/`ENV`.** They're readable via `docker history`. Use BuildKit secrets.
- **Shell-form `CMD`.** Breaks graceful shutdown. Use the JSON array (exec) form.
- **Running as root.** Default is root; add a `USER` for anything production-facing.
- **Forgetting to clean package caches** in the same `RUN` — leftover cache is baked into the layer forever.

---

## ✅ Knowledge Check

1. What's the difference between `RUN` and `CMD`?
2. Why put `COPY package.json` before `COPY . .`?
3. Does `EXPOSE 8080` make port 8080 reachable from your browser? Why or why not?
4. Why prefer the exec form of `CMD` over the shell form?

<details>
<summary>Answers</summary>

1. `RUN` executes at build time and bakes changes into the image; `CMD` runs at container start.
2. Dependencies change rarely; copying them first lets the expensive install layer stay cached across code changes.
3. No — `EXPOSE` is only metadata/documentation. You need `-p 8080:8080` at runtime.
4. Exec form makes your app PID 1, so it receives `SIGTERM` and shuts down gracefully; shell form wraps it in `/bin/sh -c` and can swallow the signal.
</details>

---

[◀ Architecture](./01-architecture.md) | [Back to README](../README.md) | [Next: Images ▶](./03-images.md)
