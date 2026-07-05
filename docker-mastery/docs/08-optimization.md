# 08 · Image Optimization (Best Practices)

[◀ Compose](./07-compose.md) | [Back to README](../README.md) | [Next: Swarm ▶](./09-swarm.md)

---

Smaller images ship faster, cost less to store, and present a smaller attack surface. This module is the practical checklist for lean, fast, secure images.

---

## 1. Multi-Stage Builds (biggest win)

Use a heavy image to *compile*, then copy only the final artifact into a tiny runtime image. Build tools, compilers, and caches never make it into production.

```dockerfile
# ---- Stage 1: build ----
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o myapp

# ---- Stage 2: runtime ----
FROM alpine:latest
WORKDIR /root/
COPY --from=builder /app/myapp .   # copy ONLY the binary
CMD ["./myapp"]
```

Result: a ~800 MB build image collapses to a ~15 MB production image. Full runnable version in [`examples/multistage-go`](../examples/multistage-go).

The same pattern works for Node, Java, Python, etc. — build/compile in one stage, copy the output into a slim final stage.

---

## 2. Choose the Right Base Image

| Base | Size | Notes |
|---|---|---|
| `ubuntu` / `debian` | ~70–120 MB | Full OS; only when you need the tooling |
| `*-slim` | ~40–80 MB | Debian minus docs/man pages |
| `*-alpine` | ~5–15 MB | Tiny, security-focused (musl libc — watch for compatibility) |
| `distroless` | ~2–20 MB | App + runtime only; no shell, no package manager |
| `scratch` | 0 MB | Empty; for fully static binaries (e.g. Go) |

> **Alpine caveat:** it uses musl instead of glibc. Some binaries/wheels expect glibc and break. Test before committing to Alpine.
>
> **Distroless caveat:** no shell means no `docker exec ... sh` for debugging — a security benefit and a debugging tradeoff.

---

## 3. Minimize Layers — Chain `RUN`s

Each `FROM`/`RUN`/`COPY`/`ADD` is a layer. Combine related commands and clean up **in the same layer**, or the cleanup doesn't shrink anything (the files are already committed to the earlier layer).

```dockerfile
# ❌ Bad — 3 layers, cache never cleaned
RUN apt-get update
RUN apt-get install -y git
RUN apt-get install -y curl

# ✅ Good — 1 layer, cache removed in the same layer
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        curl \
    && rm -rf /var/lib/apt/lists/*
```

---

## 4. Order for Cache Efficiency

Docker caches layers top-down. Put rarely-changing steps first, frequently-changing steps (your code) last.

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package.json package-lock.json ./   # changes rarely
RUN npm ci                               # cached across code edits
COPY . .                                 # changes constantly → last
```

---

## 5. Use `.dockerignore`

Stop unnecessary/secret files from entering the build context. Faster builds, smaller and safer images.

```gitignore
.git
node_modules
dist
target
*.log
.env
```

---

## 6. Install Only What You Need

Don't bake `vim`, `curl`, or debug tools into production images — each is attack surface. Debug with `docker exec` or a throwaway debug container instead. Use `--no-install-recommends` (apt) and `--omit=dev` / `--production` (npm) to skip extras.

---

## 7. Pin Specific Tags (avoid `:latest`)

`:latest` is a moving target — a base update can break you silently. Pin exact versions for reproducible, stable builds.

```dockerfile
FROM node:18.19.0-alpine     # not node:latest
```

---

## 8. Run as Non-Root

A smaller *and* safer image drops root:

```dockerfile
RUN addgroup -S app && adduser -S app -G app
USER app
```

---

## Summary Checklist

| Strategy | Benefit |
|---|---|
| Multi-stage builds | Drops final image size dramatically |
| Alpine / slim / distroless base | Smallest footprint, less attack surface |
| Chain `RUN` + clean caches | Fewer, leaner layers |
| Dependency-first ordering | Faster rebuilds via cache |
| `.dockerignore` | Smaller context, no leaked secrets |
| No debug tools in prod | Less attack surface |
| Pinned tags | Reproducible builds |
| Non-root `USER` | Safer runtime |

---

## 🧪 Lab

See [labs/labs.md → Lab 8](../labs/labs.md#lab-8--shrink-an-image-with-multi-stage). Build the Go example naively, then with a multi-stage Dockerfile, and compare `docker images` sizes.

```bash
cd examples/multistage-go
docker build -t go-fat -f Dockerfile.naive .
docker build -t go-slim -f Dockerfile .
docker images | grep go-
```

---

## ⚠️ Common Pitfalls

- **Cleaning caches in a separate `RUN`.** The files are already committed to the earlier layer; cleanup must be in the *same* `RUN`.
- **Switching to Alpine blindly.** musl vs glibc breaks some binaries; test first.
- **Copying source before dependencies.** Destroys the cache advantage.
- **Leaving build tools in the final image.** That's exactly what multi-stage builds exist to prevent.
- **`:latest` in production.** Non-reproducible; pin versions.

---

## ✅ Knowledge Check

1. What problem do multi-stage builds solve?
2. Why must `apt-get` cache cleanup be in the same `RUN` as the install?
3. Give one risk of switching a base image to Alpine.
4. Why avoid `:latest` for production images?

<details>
<summary>Answers</summary>

1. They keep heavy build tools/compilers out of the final image by copying only the built artifact into a slim runtime stage.
2. Layers are immutable; if cleanup is a later `RUN`, the cache files are already committed to the earlier layer and still bloat the image.
3. Alpine uses musl (not glibc), which can break binaries/wheels that expect glibc.
4. It's a moving pointer — base updates can change behavior and break reproducibility.
</details>

---

[◀ Compose](./07-compose.md) | [Back to README](../README.md) | [Next: Swarm ▶](./09-swarm.md)
