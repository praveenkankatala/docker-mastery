# 🐳 Docker Mastery — From Zero to Production

A structured, **hands-on** guide to Docker. Every module pairs the theory with commands you can actually run, a lab to practice, common pitfalls, and a knowledge check. Runnable example projects live in [`examples/`](./examples).

> This is a practitioner's reference. If you can build an image, persist data with a volume, wire services together on a custom network with Compose, and secure and optimize the result — you can ship Docker in production.

---

## 📋 Prerequisites

| Requirement | Notes |
|---|---|
| Docker Engine 24+ (or Docker Desktop) | `docker --version` |
| Docker Compose v2 | Ships with Desktop / `docker-compose-plugin`. Invoked as `docker compose` (space, not hyphen). |
| A terminal + basic Linux CLI | `cd`, `ls`, editing text files |
| ~5 GB free disk | Images and volumes add up |

Verify your install:

```bash
docker run --rm hello-world
```

If you see the welcome message, you're ready. The `--rm` flag auto-deletes the container when it exits, so it leaves nothing behind.

---

## 🗺️ Learning Path

Work through the modules in order. Each builds on the previous one.

| # | Module | What you'll be able to do |
|---|--------|---------------------------|
| 01 | [Architecture & Core Concepts](./docs/01-architecture.md) | Explain the client/daemon/registry model and why containers ≠ VMs |
| 02 | [Dockerfile Deep Dive](./docs/02-dockerfile.md) | Write a correct, cache-friendly Dockerfile and understand every instruction |
| 03 | [Images](./docs/03-images.md) | Build, tag, inspect, and manage images and their layers |
| 04 | [Containers & Lifecycle](./docs/04-containers.md) | Run, inspect, exec into, and clean up containers |
| 05 | [Storage & Volumes](./docs/05-storage-volumes.md) | Persist and share data correctly across container restarts |
| 06 | [Networking](./docs/06-networking.md) | Connect containers by name using custom networks and DNS |
| 07 | [Docker Compose](./docs/07-compose.md) | Define and run multi-container stacks from one YAML file |
| 08 | [Image Optimization](./docs/08-optimization.md) | Cut image size and build time; multi-stage builds |
| 09 | [Docker Swarm](./docs/09-swarm.md) | Orchestrate containers across multiple hosts |
| 10 | [Security & Advanced Topics](./docs/10-security-advanced.md) | Rootless mode, secrets, Buildx, scanning, private registry, CI/CD |
| — | [CLI Cheat Sheet](./docs/cheatsheet.md) | Every command in one place |

**Hands-on labs:** [`labs/`](./labs) — self-contained exercises you can do after each module.

---

## 📁 Repository Structure

```
docker-mastery/
├── README.md                     ← you are here
├── docs/                         ← the 10 learning modules + cheat sheet
│   ├── 01-architecture.md
│   ├── 02-dockerfile.md
│   ├── 03-images.md
│   ├── 04-containers.md
│   ├── 05-storage-volumes.md
│   ├── 06-networking.md
│   ├── 07-compose.md
│   ├── 08-optimization.md
│   ├── 09-swarm.md
│   ├── 10-security-advanced.md
│   └── cheatsheet.md
├── labs/
│   └── labs.md                   ← guided exercises
└── examples/                     ← real, runnable projects
    ├── flask-redis/              ← Compose: web app + Redis
    ├── multistage-go/            ← multi-stage build (~800MB → ~15MB)
    ├── node-optimized/           ← cache-friendly Node image + .dockerignore
    └── three-tier-app/           ← nginx + API + Postgres, two networks, volumes
```

---

## ⚡ 60-Second Mental Model

```
   Dockerfile  ──build──▶   Image   ──run──▶   Container
   (the recipe)          (the frozen meal)   (the meal on your plate)
                              │
                        push │ pull
                              ▼
                          Registry
                     (Docker Hub / ECR / ACR)
```

- **Image** = read-only template, built in stacked layers.
- **Container** = a running instance of an image, with a thin writable layer on top.
- **Volume** = data that lives *outside* the container so it survives deletion.
- **Network** = how containers find and talk to each other (by service name).
- **Compose** = one file to declare a whole multi-container stack.
- **Swarm** = run that stack across many machines, with self-healing.

---

## ✅ How to Use This Repo

1. Read a module in `docs/`.
2. Run the commands as you go — don't just read them.
3. Do the matching lab in `labs/labs.md`.
4. Check yourself against the "Knowledge Check" at the end of each module.
5. When stuck, the [cheat sheet](./docs/cheatsheet.md) has the syntax.

---

## 📝 License

MIT — use it, fork it, share it. See [LICENSE](./LICENSE).

## 🤝 Contributing

Corrections and additions welcome. Open an issue or a PR. Keep the "theory → command → lab → pitfall" structure consistent across modules.
