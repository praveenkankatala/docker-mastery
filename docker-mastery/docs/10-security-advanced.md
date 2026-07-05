# 10 · Security & Advanced Topics

[◀ Swarm](./09-swarm.md) | [Back to README](../README.md) | [Cheat Sheet ▶](./cheatsheet.md)

---

The Gemini chat stopped at Swarm. This module covers the topics that separate "I can run containers" from "I can run containers **in production, safely**": security hardening, rootless mode, secrets, Buildx multi-arch, image scanning, private registries, and CI/CD.

---

## 1. Container Security Hardening

Security is layered. Apply as many of these as fit your workload:

**Run as non-root.** By default the container process is root (mapped to host root). Drop it:

```dockerfile
RUN addgroup -S app && adduser -S app -G app
USER app
```

**Read-only root filesystem.** Prevent tampering; allow writes only where needed via tmpfs/volumes:

```bash
docker run --read-only --tmpfs /tmp my-app
```

**Drop Linux capabilities.** Containers get a set of kernel capabilities by default. Drop all, add back only what's required:

```bash
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE my-app
```

**Prevent privilege escalation:**

```bash
docker run --security-opt=no-new-privileges my-app
```

**Set resource limits** (a DoS defense — see [Module 01](./01-architecture.md)):

```bash
docker run --memory=512m --cpus=1.0 --pids-limit=100 my-app
```

**Never use `--privileged`** unless you truly must — it grants near-host access and defeats most isolation.

**Minimal base images** (distroless/scratch) shrink the attack surface — no shell for an attacker to use ([Module 08](./08-optimization.md)).

### Quick hardening checklist

| Control | Flag / directive |
|---|---|
| Non-root user | `USER app` |
| Read-only FS | `--read-only` |
| Drop capabilities | `--cap-drop=ALL` |
| No privilege escalation | `--security-opt=no-new-privileges` |
| Resource caps | `--memory`, `--cpus`, `--pids-limit` |
| Avoid | `--privileged` |

---

## 2. Rootless Mode

By default `dockerd` runs as **root**, so a container escape can mean host root. **Rootless mode** runs the daemon and containers as an unprivileged user via **user namespaces**, so even a breakout only gets an unprivileged host account.

```bash
# Install/enable rootless (Linux)
dockerd-rootless-setuptool.sh install
export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock
docker info | grep -i rootless
```

**Tradeoffs:** can't bind ports below 1024 without extra config; some storage drivers and network modes are limited. Excellent for shared/multi-tenant hosts and CI runners.

---

## 3. Secrets Management

**The problem:** `ENV` and `ARG` bake values into image layers, readable via `docker history`. **Never** put passwords/keys there.

### BuildKit build secrets (at build time)

Mount a secret for a single `RUN` without persisting it in any layer:

```dockerfile
# syntax=docker/dockerfile:1
RUN --mount=type=secret,id=npmtoken \
    NPM_TOKEN=$(cat /run/secrets/npmtoken) npm ci
```

```bash
DOCKER_BUILDKIT=1 docker build --secret id=npmtoken,src=./npm_token.txt -t app .
```

### Docker Swarm secrets (at runtime)

Swarm encrypts secrets and mounts them as files (in-memory, at `/run/secrets/<name>`), never in env vars:

```bash
echo "s3cr3t" | docker secret create db_password -
docker service create --name db --secret db_password postgres:16
# app reads /run/secrets/db_password
```

### Compose runtime secrets

```yaml
services:
  db:
    image: postgres:16
    secrets:
      - db_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
secrets:
  db_password:
    file: ./db_password.txt
```

> For anything serious, use a dedicated secrets manager (AWS Secrets Manager, HashiCorp Vault, Azure Key Vault) and inject at runtime.

---

## 4. Buildx & Multi-Architecture Builds

**Buildx** (BuildKit-powered) builds a single image that runs on multiple CPU architectures — e.g. Intel/AMD (`amd64`) **and** ARM (Apple Silicon, AWS Graviton).

```bash
# Create and use a builder
docker buildx create --name multi --use

# Build & push a multi-arch image in one shot
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t myuser/myapp:1.0 \
  --push .
```

The registry stores a **manifest list**; each host automatically pulls the variant for its architecture. BuildKit also gives you faster parallel builds, better caching, and the `--mount=type=secret` / `--mount=type=cache` features. BuildKit is the default builder in modern Docker.

```dockerfile
# Cache mount example — persist package cache across builds
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt
```

---

## 5. Image Scanning & Supply-Chain Security

Images pull in OS packages and dependencies with known CVEs. **Scan before you ship.**

```bash
# Docker's built-in scan (Scout)
docker scout cves myapp:1.0
docker scout quickview myapp:1.0

# Popular open-source scanner
trivy image myapp:1.0
```

Related supply-chain practices:

- **SBOM** (Software Bill of Materials): `docker scout sbom` / `trivy image --format spdx`.
- **Image signing:** sign images (e.g. with cosign) so consumers can verify provenance.
- **Pin base image digests** (`FROM node:18-alpine@sha256:...`) for immutable, verifiable bases.

---

## 6. Hosting a Private Registry

Keep proprietary images off public Docker Hub. Options: managed (**AWS ECR, Azure ACR, GCP Artifact Registry, GitHub GHCR**) or self-hosted with the open-source `registry` image.

```bash
# Run a local private registry
docker run -d -p 5000:5000 --name registry registry:2

# Push to it
docker tag myapp:1.0 localhost:5000/myapp:1.0
docker push localhost:5000/myapp:1.0
docker pull localhost:5000/myapp:1.0
```

Production registries add TLS, authentication, and access control. Example — log in to GHCR:

```bash
echo $TOKEN | docker login ghcr.io -u USERNAME --password-stdin
docker push ghcr.io/USERNAME/myapp:1.0
```

---

## 7. CI/CD Pipeline Integration

Automate the Docker flow: on every push, **build → scan → push → deploy**. Example GitHub Actions workflow:

```yaml
name: docker
on:
  push:
    branches: [main]

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:latest
          platforms: linux/amd64,linux/arm64
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

The same idea maps to GitLab CI, Jenkins, AWS CodeBuild, Azure Pipelines: a runner with Docker builds the image, an image scan gates the pipeline, then `docker push` to your registry and a deploy step rolls it out.

---

## 8. Observability & Housekeeping

```bash
docker system df            # disk used by images/containers/volumes/cache
docker system prune         # remove stopped containers, unused nets, dangling images
docker system prune -a --volumes   # aggressive: also unused images + volumes (careful!)
docker events               # live stream of daemon events
docker logs --since 1h app  # time-bounded logs
```

Configure a **logging driver** (`json-file` with rotation, or ship to `awslogs`, `fluentd`, Loki) so container logs don't fill the disk:

```bash
docker run --log-driver=json-file --log-opt max-size=10m --log-opt max-file=3 app
```

---

## 🧪 Lab

See [labs/labs.md → Lab 10](../labs/labs.md#lab-10--harden-scan-and-registry). Run a hardened container (non-root, read-only, dropped caps), scan an image for CVEs, and push to a local private registry.

---

## ⚠️ Common Pitfalls

- **Secrets in `ENV`/`ARG`.** Readable in image history forever. Use BuildKit/Swarm/Compose secrets or a vault.
- **Running `--privileged` "to make it work."** You've just removed most of your isolation.
- **Never scanning images.** You ship known CVEs. Add `docker scout`/`trivy` to CI as a gate.
- **`docker system prune -a --volumes` without thinking.** Can delete volumes/data you needed.
- **Unbounded logs.** No log rotation → disk fills → daemon and host misbehave.
- **Trusting `:latest` from public registries.** Pin digests and prefer scanned, signed images.

---

## ✅ Knowledge Check

1. Why is putting a password in `ENV` unsafe even if the container is private?
2. What does rootless mode protect against?
3. What problem does `docker buildx --platform linux/amd64,linux/arm64` solve?
4. Name two things a CI pipeline should do between `build` and `push`.

<details>
<summary>Answers</summary>

1. `ENV`/`ARG` values are baked into image layers and visible via `docker history` to anyone who gets the image.
2. A container escape only yields an unprivileged host account (the daemon/containers run without host root).
3. Produces one image that runs natively on both Intel/AMD and ARM hosts via a manifest list.
4. Scan for CVEs (gate the build) and optionally generate an SBOM / sign the image before pushing.
</details>

---

[◀ Swarm](./09-swarm.md) | [Back to README](../README.md) | [Cheat Sheet ▶](./cheatsheet.md)
