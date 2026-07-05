# 06 · Docker Networking

[◀ Storage & Volumes](./05-storage-volumes.md) | [Back to README](../README.md) | [Next: Compose ▶](./07-compose.md)

---

Networking lets containers talk to **each other**, to the **host**, and to the **outside world**. Without it, a container is an island. Docker solves this with pluggable **network drivers** and software-defined networking.

---

## 1. Network Drivers

### A. Bridge (default)

Docker creates a software switch (`docker0`) on the host. Containers get a private internal IP (e.g. `172.17.0.2`) and can reach each other and the internet (via NAT), but are hidden from the outside until you publish a port.

```
  Internet
     │  (NAT via -p)
┌────▼──────────── HOST ────────────────┐
│         docker0 bridge                │
│   ┌──────────┐      ┌──────────┐      │
│   │container1│──────│container2│      │
│   │172.17.0.2│      │172.17.0.3│      │
│   └──────────┘      └──────────┘      │
└───────────────────────────────────────┘
```

- **Default bridge:** containers can talk by **IP only**, not by name — so it's fragile (IPs change on restart).
- **User-defined bridge:** adds automatic **DNS resolution by container name** (see §2). **Always create your own.**

### B. Host

Removes network isolation — the container shares the host's network stack directly. If it listens on port 80, it grabs the host's port 80. Fastest (no NAT), but no isolation and port conflicts are easy. (Full support on Linux; limited on Docker Desktop for Mac/Windows.)

```bash
docker run -d --network host nginx
```

### C. None

Total isolation — only a loopback interface, no external connectivity. Good for batch jobs that must not touch the network.

```bash
docker run --network none alpine
```

### D. Overlay (multi-host)

Spans multiple physical hosts, used by **Docker Swarm**. A container on Server A talks to one on Server B as if on the same wire, traffic encrypted. See [Module 09](./09-swarm.md).

### E. Macvlan

Gives the container its own MAC address so it appears as a **physical device** on your LAN, with an IP from your router. For legacy apps that expect to sit directly on the network.

| Driver | Scope | Use case |
|---|---|---|
| bridge | Single host | Default; standalone apps |
| host | Single host | Max performance, no isolation |
| none | Single host | Fully offline containers |
| overlay | Multi-host | Swarm clusters |
| macvlan | Single host | App needs a real LAN identity |

---

## 2. DNS & Service Discovery (the killer feature)

**How does the web container find the db container?**

On the **default** bridge, only by IP — and IPs change on restart, so it's useless for stable connections.

On a **user-defined** bridge, Docker runs an embedded **DNS server**. Containers resolve each other by **name**:

```bash
docker network create app-net
docker run -d --name db  --network app-net postgres:16
docker run -d --name web --network app-net my-web

# Inside web, this just works:
#   psql -h db -U postgres
# Docker resolves "db" → its current IP automatically.
```

You never hardcode IPs. Your app connects to `postgres`, `redis`, `db` by name.

---

## 3. Port Mapping (reaching containers from outside)

Bridge containers have private IPs, so your browser can't reach them until you **publish** a port.

```bash
docker run -d -p 8080:80 nginx
#              │     │
#              │     └─ container port
#              └─ host port
```

```
Browser → localhost:8080 → Docker → container:80
```

Variations:

```bash
-p 8080:80            # host 8080 → container 80
-p 127.0.0.1:8080:80  # bind only to localhost (not exposed on the LAN)
-p 80                 # random high host port → container 80
-P                    # publish all EXPOSEd ports to random host ports
```

---

## 4. Under the Hood

- **Network namespaces:** each container gets its own isolated network stack — its own `eth0`, routing table, and iptables rules.
- **veth pairs (virtual ethernet):** Docker creates a virtual cable. One end (`eth0`) sits inside the container; the other (`veth…`) plugs into the host bridge. Packets cross from the isolated namespace to the host through this pair.

---

## 5. Essential Commands

```bash
docker network ls                       # list networks
docker network create app-net           # create a user-defined bridge
docker network create -d overlay my-ov  # create an overlay (Swarm)
docker network inspect app-net          # subnet, gateway, connected containers
docker network connect app-net web      # attach a running container
docker network disconnect app-net web   # detach
docker network prune                    # remove unused networks
```

A container can be attached to **multiple** networks — that's how you isolate tiers (see the three-tier example below and in [`examples/three-tier-app`](../examples/three-tier-app)).

---

## 6. Real-World Isolation Pattern

Put a database on a **private** network the frontend can't reach:

```
Internet ──▶ [frontend] ──frontend-net──▶ [backend] ──backend-net──▶ [database]
                                                                       (no path
                                                                        from frontend)
```

- `frontend` ∈ `frontend-net` only.
- `backend` ∈ `frontend-net` **and** `backend-net`.
- `database` ∈ `backend-net` only.

Because the frontend isn't on `backend-net`, a compromised frontend still can't talk to the database directly. Compose makes this trivial ([Module 07](./07-compose.md)).

---

## 🧪 Lab

See [labs/labs.md → Lab 6](../labs/labs.md#lab-6--connect-two-containers-by-name). Create a custom network, run two containers, and ping one from the other **by name** — then try the same on the default bridge and watch it fail.

---

## ⚠️ Common Pitfalls

- **Using the default bridge.** No name-based DNS → you're stuck hardcoding IPs. Always `docker network create`.
- **`EXPOSE` instead of `-p`.** `EXPOSE` is documentation; `-p` actually publishes.
- **Publishing DB ports to the world.** Don't `-p 5432:5432` your database — keep it internal on a private network.
- **Port conflicts.** "port is already allocated" → another process/container already owns that host port.
- **Assuming host networking works everywhere.** It's Linux-native; behaves differently on Docker Desktop.

---

## ✅ Knowledge Check

1. Why can't containers resolve each other by name on the *default* bridge?
2. What does `-p 8080:80` do, and which number is the host port?
3. How would you keep a database unreachable from a public frontend container?
4. What are veth pairs?

<details>
<summary>Answers</summary>

1. The default bridge has no embedded DNS for container names; only user-defined bridges provide name resolution.
2. Publishes host port **8080** to container port 80; the first number (8080) is the host port.
3. Put the DB on a private network the frontend isn't attached to; the backend bridges the two networks.
4. Virtual ethernet "cables" — one end is the container's `eth0`, the other plugs into the host bridge, carrying packets across the namespace boundary.
</details>

---

[◀ Storage & Volumes](./05-storage-volumes.md) | [Back to README](../README.md) | [Next: Compose ▶](./07-compose.md)
