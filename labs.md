# 🧪 Hands-On Labs

[◀ Back to README](../README.md)

Ten labs, one per module. Each is self-contained: **Goal → Steps → What you learned → Cleanup.** Run them in order.

> All labs clean up after themselves. If something goes sideways, `docker rm -f $(docker ps -aq)` removes every container.

---

## Lab 1 · Your First Container & Resource Limits

**Module:** [01 Architecture](../docs/01-architecture.md)

**Goal:** verify Docker works and see cgroup limits enforced.

```bash
docker run --rm hello-world                       # 1. verify install
docker run -d --name limited --memory=256m nginx  # 2. run with a memory cap
docker stats --no-stream limited                  # 3. confirm "/ 256MiB" in LIMIT column
docker exec limited cat /proc/1/cgroup            # 4. peek at cgroup membership
docker rm -f limited                              # 5. clean up
```

**You learned:** containers are just processes with kernel-enforced limits; `docker stats` proves the cap is real.

---

## Lab 2 · Write and Build a Dockerfile

**Module:** [02 Dockerfile](../docs/02-dockerfile.md)

**Goal:** build an image and prove the layer cache works.

```bash
mkdir lab2 && cd lab2
cat > app.js <<'EOF'
require('http').createServer((_, res) => res.end('v1')).listen(3000);
EOF
cat > Dockerfile <<'EOF'
FROM node:18-alpine
WORKDIR /app
COPY app.js .
EXPOSE 3000
CMD ["node", "app.js"]
EOF

docker build -t lab2:1 .          # first build
docker build -t lab2:1 .          # rebuild — every step says "CACHED"

# Change the code, rebuild, watch only the COPY layer rebuild
sed -i 's/v1/v2/' app.js
docker build -t lab2:2 .

docker run --rm -d -p 3000:3000 --name lab2 lab2:2
curl localhost:3000               # → v2
docker rm -f lab2 && cd .. && rm -rf lab2
```

**You learned:** unchanged layers are cached; a code change only invalidates layers from that point down.

---

## Lab 3 · Inspect Image Layers

**Module:** [03 Images](../docs/03-images.md)

**Goal:** see layers and create/prune a dangling image.

```bash
docker pull nginx:alpine
docker history nginx:alpine        # each layer + the instruction that made it
docker inspect nginx:alpine | grep -i architecture

# Create a dangling image by rebuilding a tag
echo -e "FROM alpine\nRUN echo one" > Dockerfile
docker build -t dtest .
echo -e "FROM alpine\nRUN echo two" > Dockerfile
docker build -t dtest .            # old image becomes <none>:<none>
docker images -f "dangling=true"   # see it
docker image prune -f              # clean it
rm Dockerfile
```

**You learned:** images are stacked layers; rebuilding a tag orphans the old image as "dangling."

---

## Lab 4 · Container Lifecycle & Exec

**Module:** [04 Containers](../docs/04-containers.md)

**Goal:** watch data die with the container.

```bash
docker run -d --name web nginx
docker exec web sh -c "echo 'hello' > /tmp/note.txt"
docker exec web cat /tmp/note.txt      # hello
docker rm -f web                       # destroy container

docker run -d --name web nginx
docker exec web cat /tmp/note.txt      # No such file — data was in the writable layer
docker rm -f web
```

**You learned:** the writable layer is destroyed with the container. (Lab 5 fixes this with a volume.)

---

## Lab 5 · Persist Data with a Volume

**Module:** [05 Storage & Volumes](../docs/05-storage-volumes.md)

**Goal:** prove a named volume survives a full recreate.

```bash
docker volume create notes
docker run -d --name web -v notes:/data nginx
docker exec web sh -c "echo 'survives' > /data/note.txt"
docker rm -f web                                   # destroy container

docker run -d --name web -v notes:/data nginx      # new container, same volume
docker exec web cat /data/note.txt                 # survives ✅
docker volume inspect notes                        # see the real host path

docker rm -f web && docker volume rm notes
```

**You learned:** data on a named volume outlives any container.

---

## Lab 6 · Connect Two Containers by Name

**Module:** [06 Networking](../docs/06-networking.md)

**Goal:** DNS resolution on a user-defined bridge vs. the default bridge.

```bash
# User-defined bridge → name resolution works
docker network create app-net
docker run -d --name db --network app-net nginx
docker run --rm --network app-net alpine sh -c "ping -c1 db"   # resolves ✅

# Default bridge → name resolution fails
docker run -d --name db2 nginx
docker run --rm alpine sh -c "ping -c1 db2" || echo "FAILED as expected"

docker rm -f db db2 && docker network rm app-net
```

**You learned:** only user-defined networks give you container-name DNS. Always create your own.

---

## Lab 7 · Multi-Container with Compose

**Module:** [07 Compose](../docs/07-compose.md)

**Goal:** run a web app + Redis with one command.

```bash
cd ../examples/flask-redis
docker compose up -d
curl localhost:8000        # counter increments (state stored in Redis)
curl localhost:8000
docker compose ps
docker compose logs --tail 20
docker compose down
```

**You learned:** Compose auto-creates a network so `web` reaches `redis` by name; one file defines the whole stack.

---

## Lab 8 · Shrink an Image with Multi-Stage

**Module:** [08 Optimization](../docs/08-optimization.md)

**Goal:** compare a naive build vs. a multi-stage build.

```bash
cd ../examples/multistage-go
docker build -t go-fat  -f Dockerfile.naive .
docker build -t go-slim -f Dockerfile .
docker images | grep -E "go-(fat|slim)"    # slim is a fraction of fat's size
docker run --rm go-slim
docker rmi go-fat go-slim
```

**You learned:** multi-stage builds copy only the compiled binary into a tiny runtime image.

---

## Lab 9 · Single-Node Swarm

**Module:** [09 Swarm](../docs/09-swarm.md)

**Goal:** deploy a service, watch self-healing, scale, and roll an update.

```bash
docker swarm init
docker service create --name web --replicas 3 -p 8080:80 nginx
docker service ps web                       # 3 tasks

# Kill one task's container — Swarm recreates it
docker rm -f $(docker ps -q -f name=web | head -1)
sleep 3 && docker service ps web            # back to 3 (self-healed)

docker service scale web=5                  # scale up
docker service update --image nginx:1.27 web   # rolling update
docker service rm web
docker swarm leave --force
```

**You learned:** you declare desired state; Swarm continuously reconciles reality to match it.

---

## Lab 10 · Harden, Scan, and Registry

**Module:** [10 Security & Advanced](../docs/10-security-advanced.md)

**Goal:** run a hardened container, scan an image, use a private registry.

```bash
# Hardened run: non-root-ish, read-only FS, no new privileges, dropped caps
docker run --rm --read-only --tmpfs /tmp \
  --cap-drop=ALL --security-opt=no-new-privileges \
  alpine sh -c "echo hardened && touch /tmp/ok && ls /tmp"

# Scan for CVEs (Docker Scout ships with Docker Desktop)
docker scout quickview nginx:alpine || echo "install docker scout to try this"

# Local private registry round-trip
docker run -d -p 5000:5000 --name registry registry:2
docker pull alpine
docker tag alpine localhost:5000/alpine:mine
docker push localhost:5000/alpine:mine
docker pull localhost:5000/alpine:mine
docker rm -f registry
```

**You learned:** how to lock down a container's runtime, gate on CVEs, and run your own registry.

---

## 🧹 Full Reset

If your machine gets cluttered:

```bash
docker rm -f $(docker ps -aq) 2>/dev/null
docker system prune -a --volumes    # nuclear: removes everything unused
```

---

[◀ Back to README](../README.md)
