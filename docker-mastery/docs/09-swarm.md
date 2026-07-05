# 09 · Docker Swarm (Orchestration)

[◀ Optimization](./08-optimization.md) | [Back to README](../README.md) | [Next: Security & Advanced ▶](./10-security-advanced.md)

---

**Docker Swarm** is Docker's built-in orchestrator. Plain Docker runs containers on **one** host; Swarm turns a pool of Docker hosts into a **single virtual cluster** and keeps your app running across them.

> If Docker is a solo musician, Swarm is the conductor of the orchestra.

---

## 1. Architecture: Nodes

```
        ┌──────────────── SWARM CLUSTER ────────────────┐
        │                                                │
        │   ┌───────────┐   Raft consensus              │
        │   │ MANAGER 1 │◀────────┐                      │
        │   └───────────┘         │                      │
        │   ┌───────────┐   ┌───────────┐                │
        │   │ MANAGER 2 │◀──│ MANAGER 3 │  (odd number   │
        │   └─────┬─────┘   └─────┬─────┘   for quorum)   │
        │         │ schedule tasks │                      │
        │   ┌─────▼─────┐   ┌─────▼─────┐  ┌───────────┐  │
        │   │ WORKER 1  │   │ WORKER 2  │  │ WORKER 3  │  │
        │   │ runs      │   │ runs      │  │ runs      │  │
        │   │ containers│   │ containers│  │ containers│  │
        │   └───────────┘   └───────────┘  └───────────┘  │
        └────────────────────────────────────────────────┘
```

**Manager nodes (the brains)** — schedule work, hold cluster state, expose the API. They use the **Raft consensus algorithm** to agree on state. Run an **odd number** (3 or 5) so a majority (quorum) survives a failure.

**Worker nodes (the muscle)** — run the actual containers (tasks) and report status back. Managers can also run tasks, but in large setups you keep them dedicated.

---

## 2. Service → Task → Container

In plain Docker you run a **container**. In Swarm you declare a **service** — a *desired state*, not a one-off command.

```
  SERVICE  "run 3 replicas of nginx"
     │  manager creates 3
     ▼
  TASK  TASK  TASK        ← scheduling slots
     │     │     │
     ▼     ▼     ▼
  CONTAINER × 3 (placed across nodes)
```

- **Service** — the declaration ("I want 3 nginx replicas on port 80").
- **Task** — one scheduling slot; maps to exactly one container.
- **Container** — the running instance a task starts.

---

## 3. Key Features

### Desired-state reconciliation (self-healing)

You declare 3 replicas. A worker crashes and one dies. The manager sees actual (2) ≠ desired (3) and schedules a replacement on a healthy node — automatically, no human involved.

### Rolling updates & rollback

Update a service's image with zero downtime — a few containers at a time, with a delay between batches. If a batch fails its healthcheck, Swarm can auto-rollback.

```bash
docker service update --image myapp:2.0 \
  --update-parallelism 2 --update-delay 10s web
```

---

## 4. Networking: The Routing Mesh

Swarm uses **overlay networks** spanning all hosts, plus an **ingress routing mesh** for load balancing.

Publish a service on port 80 and Swarm opens port 80 on **every** node. A request to *any* node's IP is transparently routed to a node actually running the container — built-in load balancing regardless of placement.

```
  Client → Node B:80 ──(routing mesh)──▶ container on Node A:80
```

---

## 5. Essential Commands

```bash
# Turn the current host into a manager (start the cluster)
docker swarm init --advertise-addr <MANAGER-IP>

# Other hosts join (token printed by swarm init)
docker swarm join --token <TOKEN> <MANAGER-IP>:2377

# Deploy a service
docker service create --name web --replicas 3 -p 80:80 nginx

docker service ls                 # list services
docker service ps web             # list tasks + which node each runs on
docker service scale web=5        # scale replicas
docker service update ...         # rolling update
docker service rm web             # remove
docker node ls                    # list cluster nodes + status
docker stack deploy -c compose.yaml mystack   # deploy a whole Compose stack to Swarm
```

> **`docker stack`** lets you deploy a Compose file to a Swarm cluster — Compose for dev, the same file (with a `deploy:` section) for the cluster.

---

## 6. Swarm vs. Kubernetes

| | Docker Swarm | Kubernetes |
|---|---|---|
| Complexity | Low, easy to learn | High, steep curve |
| Setup | Built into Docker | Separate install/tooling |
| Scale | Small–medium clusters | Massive, enterprise scale |
| Flexibility | Opinionated ("the Docker way") | Highly extensible |
| Ecosystem | Minimal | Huge (Helm, operators, CRDs…) |
| Best for | Small teams, simple apps, fast start | Large orgs, complex microservices |

> **Reality check:** the industry has largely standardized on Kubernetes for production orchestration. Swarm is still an excellent way to *learn* orchestration concepts (desired state, services, rolling updates, overlay networking) with far less overhead, and it's fine for small deployments. The mental models transfer directly to Kubernetes.

---

## 🧪 Lab

See [labs/labs.md → Lab 9](../labs/labs.md#lab-9--single-node-swarm). Init a single-node swarm, deploy a 3-replica service, kill a task and watch it self-heal, then scale and roll an update.

```bash
docker swarm init
docker service create --name web --replicas 3 -p 8080:80 nginx
docker service ps web
docker service scale web=5
docker service update --image nginx:1.27 web
docker swarm leave --force     # tear down
```

---

## ⚠️ Common Pitfalls

- **Even number of managers.** Raft needs a majority; use 3 or 5, never 2/4.
- **Confusing service with container.** You manage the *desired state* (replicas), not individual containers.
- **Expecting node-local volumes to follow tasks.** A local volume on Node A doesn't move when a task reschedules to Node B — use a shared/networked volume driver for stateful services.
- **Publishing without understanding the mesh.** Any node's IP serves the port; plan your external load balancer accordingly.

---

## ✅ Knowledge Check

1. Why run an odd number of manager nodes?
2. What's the difference between a service, a task, and a container?
3. What does "desired-state reconciliation" do when a worker crashes?
4. How does the routing mesh let you hit a container that isn't on the node you contacted?

<details>
<summary>Answers</summary>

1. Raft consensus needs a quorum (majority); an odd number maximizes fault tolerance and avoids split-brain ties.
2. Service = declared desired state; Task = one scheduling slot; Container = the running instance a task launches.
3. The manager detects actual replicas < desired and schedules replacements on healthy nodes to restore the count.
4. Swarm opens the published port on every node; the ingress routing mesh forwards the request to a node actually running the container.
</details>

---

[◀ Optimization](./08-optimization.md) | [Back to README](../README.md) | [Next: Security & Advanced ▶](./10-security-advanced.md)
