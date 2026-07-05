# 03 · Docker Images

[◀ Dockerfile](./02-dockerfile.md) | [Back to README](../README.md) | [Next: Containers ▶](./04-containers.md)

---

A **Docker image** is a read-only, standalone, executable package containing everything an app needs: code, runtime, libraries, environment variables, and config.

> If a container is a live performance, the image is the script.

---

## 1. Images Are Built in Layers (Union Filesystem)

An image is **not** one solid blob. Every Dockerfile instruction adds a **read-only layer**, stacked via a union filesystem.

```
        ┌─────────────────────────────┐  ← thin WRITABLE layer (added when you RUN a container)
        ├─────────────────────────────┤
Layer 4 │ COPY . .                     │ ┐
Layer 3 │ RUN npm ci                   │ │  read-only
Layer 2 │ WORKDIR /app                 │ │  image layers
Layer 1 │ FROM node:18-alpine          │ ┘
        └─────────────────────────────┘
```

- Layers are **immutable** — once built, never changed.
- When you run a container, Docker adds a thin **writable layer** on top. All runtime changes live there.
- To "update" an image you build a **new** image; you never edit an existing one.

---

## 2. Key Properties

**Immutability** — the image that works on your laptop behaves identically in production. Reproducibility comes free.

**Portability** — the image carries its whole environment (OS libs, runtime version), so it moves across Mac → Windows → Linux cloud unchanged.

**Efficiency via shared layers** — if ten images all use `FROM ubuntu:22.04`, that Ubuntu layer is stored **once** on disk and shared. This also speeds up pulls: only missing layers download.

---

## 3. How Images Are Identified

| Identifier | Example | Notes |
|---|---|---|
| **Image ID** | `sha256:a1b2c3…` | Unique content hash of the build |
| **Repository:Tag** | `myapp:1.0`, `python:3.12-slim` | Human-readable name + version |

If you omit the tag, Docker assumes `:latest` — which is a *moving pointer*, not a fixed version. **Pin explicit tags in production** for reproducibility.

Naming for a registry:

```
registry-host/namespace/repository:tag
────────────  ─────────  ──────────  ───
ghcr.io       / myorg   / myapp    : 1.0
```

---

## 4. Managing Images

```bash
docker images                 # list local images
docker images -a              # include intermediate layers
docker images -q              # IDs only (great for scripting)

docker pull nginx:1.27        # download from a registry
docker build -t myapp:1.0 .   # build from a Dockerfile in current dir
docker tag myapp:1.0 myapp:latest   # add another tag to the same image

docker inspect myapp:1.0      # full JSON metadata (OS, arch, env, layers)
docker history myapp:1.0      # show each layer and the instruction that made it

docker rmi myapp:1.0          # remove an image
docker image prune            # remove dangling (<none>) images
docker image prune -a         # remove ALL unused images (careful!)
```

### `docker images` output columns

| Column | Meaning |
|---|---|
| `REPOSITORY` | Image name |
| `TAG` | Version tag |
| `IMAGE ID` | Short hash |
| `CREATED` | When it was built |
| `SIZE` | Disk footprint (all layers) |

### Useful filters & formatting

```bash
# Only nginx images
docker images nginx

# Dangling images (old builds that lost their tag → wasted space)
docker images -f "dangling=true"

# Custom columns
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# Delete every image at once (IDs piped in)
docker rmi $(docker images -q)
```

---

## 5. Dangling Images

When you rebuild `myapp:1.0`, the old image loses its tag and shows as `<none>:<none>`. These **dangling images** waste disk.

```bash
docker images -f "dangling=true"   # see them
docker image prune                 # clean them up (dangling only)
```

---

## 6. Pushing to a Registry

```bash
docker login                                  # Docker Hub
docker tag myapp:1.0 myuser/myapp:1.0         # tag with your namespace
docker push myuser/myapp:1.0                  # upload

# Private registries — tag with the host prefix
docker tag myapp:1.0 123456.dkr.ecr.us-east-1.amazonaws.com/myapp:1.0
docker push 123456.dkr.ecr.us-east-1.amazonaws.com/myapp:1.0
```

---

## Image vs Container — the crucial distinction

| | Image | Container |
|---|---|---|
| State | Static (does nothing) | Active (a running process) |
| Mutability | Read-only | Writable top layer |
| Lives on | Disk | RAM + CPU (a process) |
| Analogy | Blueprint | The building |

---

## 🧪 Lab

See [labs/labs.md → Lab 3](../labs/labs.md#lab-3--inspect-image-layers). Build an image, inspect its layers with `docker history`, then create a dangling image and prune it.

---

## ⚠️ Common Pitfalls

- **Relying on `:latest`.** It moves; a base-image update can silently break you. Pin versions.
- **Never pruning.** Dangling images and old builds quietly eat gigabytes. Run `docker image prune` periodically.
- **`docker image prune -a` on a shared machine.** It removes *all* unused images, including ones others need.
- **Confusing image size with container size.** Ten containers from one image share the read-only layers; only their thin writable layers differ.

---

## ✅ Knowledge Check

1. Why can ten images sharing a base layer save so much disk?
2. What is a dangling image and how do you remove one?
3. What does `:latest` actually mean, and why avoid it in production?
4. Where do runtime file changes go when a container writes a file?

<details>
<summary>Answers</summary>

1. The shared read-only layer is stored once and referenced by all ten images.
2. An untagged (`<none>:<none>`) leftover from a rebuild; remove with `docker image prune`.
3. It's a default *moving* tag pointer, not a fixed version — the underlying image can change unexpectedly. Pin explicit versions.
4. Into the container's thin writable layer (lost when the container is deleted, unless a volume is mounted).
</details>

---

[◀ Dockerfile](./02-dockerfile.md) | [Back to README](../README.md) | [Next: Containers ▶](./04-containers.md)
