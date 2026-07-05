# 01 · Docker Architecture & Core Concepts

[◀ Back to README](../README.md) | [Next: Dockerfile ▶](./02-dockerfile.md)

---

## 1. The Client–Server Model

Docker is split into a **client** you talk to and a **daemon** that does the work. They communicate over a REST API (a local Unix socket by default, or TCP over a network).

```
        YOU
         │  docker run nginx
         ▼
┌──────────────────┐        REST API        ┌───────────────────────────┐
│  Docker Client   │ ─────────────────────▶ │      Docker Host          │
│   (docker CLI)   │                        │  ┌─────────────────────┐  │
└──────────────────┘                        │  │  Docker Daemon      │  │
                                            │  │  (dockerd)          │  │
                                            │  │  builds, runs,      │  │
                                            │  │  manages objects    │  │
                                            │  └─────────┬───────────┘  │
                                            │     images │ containers   │
                                            │   networks │ volumes      │
                                            └────────────┼──────────────┘
                                                         │ pull / push
                                                         ▼
                                            ┌───────────────────────────┐
                                            │        Registry           │
                                            │  Docker Hub / ECR / ACR   │
                                            └───────────────────────────┘
```

**Kitchen analogy:** the client is the waiter taking your order, the daemon is the kitchen that cooks it, and the registry is the pantry storing the recipes and ingredients.

### The three pillars

| Component | Role |
|---|---|
| **Docker Client** (`docker`) | The CLI. Translates your commands into API calls. |
| **Docker Host** | The machine (physical or VM) running `dockerd`, which manages images, containers, networks, and volumes. |
| **Docker Registry** | Stores and distributes images. Public (Docker Hub) or private (AWS ECR, Azure ACR, self-hosted). |

> **Under the daemon:** modern Docker doesn't run containers directly. `dockerd` delegates to **containerd** (a container runtime), which in turn uses **runc** to create the container using kernel features. You rarely touch these, but knowing the chain (`dockerd → containerd → runc`) helps when debugging low-level issues.

---

## 2. The Docker Flow: Build → Ship → Run

```
  BUILD                     SHIP                      RUN
┌────────────┐   push    ┌────────────┐   pull    ┌────────────┐
│ Dockerfile │ ───────▶  │  Registry  │ ───────▶  │  Container │
│  + code    │   Image   │  (stored)  │   Image   │  (running) │
└────────────┘           └────────────┘           └────────────┘
 docker build            docker push               docker run
```

| Step | Command | Input | Output |
|---|---|---|---|
| **Build** | `docker build` | Dockerfile + code | Image (local) |
| **Ship** | `docker push` | Image | Image stored in registry |
| **Pull** | `docker pull` | Image name | Image (local) |
| **Run** | `docker run` | Image | Container |

**Why this matters:** the *exact same image* built on your laptop is the one that runs in production. The environment is baked into the image, which kills the "works on my machine" problem.

> On `docker run`, if the image isn't present locally the daemon performs an implicit `pull` first, then creates the writable layer, attaches a network interface, and starts the process.

---

## 3. How Docker Talks to the Kernel

This is the single most important idea for understanding *why* containers are fast. **Containers share the host's kernel** — Docker does not boot a new OS per container. It uses two Linux kernel features to create the illusion of isolation:

### A. Namespaces — *what a container can see* (isolation)

Namespaces partition kernel resources so a container only sees its own slice.

| Namespace | Effect |
|---|---|
| **PID** | The container's main process is PID 1, even if it's PID 4000 on the host |
| **NET** | Its own IP, routing table, and network interfaces |
| **MNT** | Its own filesystem mounts |
| **UTS** | Its own hostname |
| **IPC** | Its own inter-process communication |
| **USER** | Maps container users to host users (basis of rootless mode) |

### B. Control Groups (cgroups) — *what a container can use* (limits)

cgroups cap how much CPU, memory, and I/O a container may consume, so one greedy container can't starve the host.

```
Host Kernel  ── "This container gets max 0.5 CPU and 512 MB RAM." ──▶  cgroups enforce it
```

**Apartment analogy:** the kernel is the building. VMs are separate houses (own foundation, plumbing, roof). Containers are apartments in one building — they share the foundation and plumbing (the kernel), namespaces give each its own locks and keys (privacy), and cgroups make sure no single tenant drains all the hot water.

---

## 4. Virtual Machines vs. Containers

The core difference is **what gets virtualized**.

```
        VIRTUAL MACHINES                          CONTAINERS
┌───────┐ ┌───────┐ ┌───────┐            ┌───────┐ ┌───────┐ ┌───────┐
│ App A │ │ App B │ │ App C │            │ App A │ │ App B │ │ App C │
├───────┤ ├───────┤ ├───────┤            ├───────┤ ├───────┤ ├───────┤
│Bins/  │ │Bins/  │ │Bins/  │            │Bins/  │ │Bins/  │ │Bins/  │
│Libs   │ │Libs   │ │Libs   │            │Libs   │ │Libs   │ │Libs   │
├───────┤ ├───────┤ ├───────┤            └───────┴─┴───────┴─┴───────┘
│Guest  │ │Guest  │ │Guest  │            ┌─────────────────────────────┐
│  OS   │ │  OS   │ │  OS   │            │      Docker Engine          │
└───────┴─┴───────┴─┴───────┘            └─────────────────────────────┘
┌─────────────────────────────┐          ┌─────────────────────────────┐
│        Hypervisor           │          │        Host OS  +  Kernel   │
└─────────────────────────────┘          └─────────────────────────────┘
┌─────────────────────────────┐          ┌─────────────────────────────┐
│         Hardware            │          │         Hardware            │
└─────────────────────────────┘          └─────────────────────────────┘
```

| Feature | Virtual Machine | Docker Container |
|---|---|---|
| Virtualizes | Hardware (via hypervisor) | The OS (shares host kernel) |
| Guest OS | Full OS per VM | None — shares host kernel |
| Size | Gigabytes | Megabytes |
| Boot time | Minutes | Milliseconds |
| Isolation | Stronger (full separation) | Process-level (shared kernel) |
| Portability | Tied to hypervisor | Run anywhere Docker runs |

### When to use which

- **VMs** — when you need a *different* kernel/OS (e.g. Windows on a Linux host) or the strongest possible isolation (multi-tenant untrusted workloads).
- **Containers** — microservices, fast CI/CD, packing many apps efficiently onto one host, reproducible dev environments.

> They're not mutually exclusive — in the cloud, containers usually run *inside* VMs (e.g. EKS nodes are EC2 VMs running many pods/containers).

---

## 5. Applying cgroup Limits in Practice

You never touch cgroups directly — you pass flags to `docker run` and Docker translates them for the kernel.

```bash
# Limit memory to 512 MB
docker run -d --memory="512m" --name web nginx

# Limit CPU to half a core
docker run -d --cpus="0.5" --name worker nginx

# Both together (production pattern)
docker run -d --name safe-app --memory="512m" --cpus="1.0" nginx
```

Verify the kernel is enforcing limits — `docker stats` is Docker's Task Manager:

```bash
docker stats
```

```
CONTAINER ID   NAME       CPU %   MEM USAGE / LIMIT
a1b2c3d4       safe-app   0.02%   4.8MiB / 512MiB
```

The `LIMIT` column confirms your cap is active.

---

## 🧪 Lab

See [labs/labs.md → Lab 1](../labs/labs.md#lab-1--your-first-container--resource-limits).

Quick version:

```bash
docker run --rm hello-world                       # verify install
docker run -d --name limited --memory=256m nginx  # run with a cap
docker stats --no-stream limited                  # confirm the 256MiB limit
docker rm -f limited                              # clean up
```

---

## ⚠️ Common Pitfalls

- **Thinking containers are VMs.** They share your kernel — a Linux container needs a Linux kernel. (On Mac/Windows, Docker Desktop runs a lightweight Linux VM behind the scenes.)
- **No resource limits in production.** Without `--memory`/`--cpus`, one container can take down the host.
- **Assuming stronger isolation than you have.** Containers share a kernel; a kernel exploit can cross the boundary. For hostile multi-tenant workloads, add VM-level isolation.

---

## ✅ Knowledge Check

1. What are the three components of the client–server model?
2. Which kernel feature provides *isolation*, and which provides *resource limits*?
3. Give two reasons a container boots in milliseconds but a VM takes minutes.
4. When would you still choose a VM over a container?

<details>
<summary>Answers</summary>

1. Docker Client, Docker Host (daemon), Registry.
2. Namespaces → isolation; cgroups → resource limits.
3. No guest OS to boot (shares host kernel); it's just starting a process, not booting hardware.
4. Different OS/kernel required, or you need stronger-than-process isolation for untrusted tenants.
</details>

---

[◀ Back to README](../README.md) | [Next: Dockerfile ▶](./02-dockerfile.md)
