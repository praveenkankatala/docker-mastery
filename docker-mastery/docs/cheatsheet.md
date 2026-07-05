# 🧾 Docker CLI Cheat Sheet

[◀ Back to README](../README.md)

A one-page reference for every command in this repo.

---

## Info & Setup

```bash
docker --version              # client/version
docker info                   # daemon status, driver, resources
docker system df              # disk usage breakdown
docker login                  # authenticate to a registry
```

## Images

```bash
docker build -t name:tag .            # build from Dockerfile in .
docker images                         # list images
docker images -q                      # IDs only
docker pull name:tag                  # download
docker push user/name:tag             # upload
docker tag src:tag new:tag            # add a tag
docker history name:tag               # show layers
docker inspect name:tag               # full metadata (JSON)
docker rmi name:tag                   # remove image
docker image prune                    # remove dangling
docker image prune -a                 # remove all unused
```

## Containers — run

```bash
docker run image                      # run (foreground)
docker run -d image                   # detached
docker run -it image bash             # interactive shell
docker run --rm image                 # auto-remove on exit
docker run --name web image           # named
docker run -p 8080:80 image           # publish port host:container
docker run -e KEY=val image           # env var
docker run -v vol:/path image         # mount volume
docker run --network net image        # attach network
docker run --restart unless-stopped image   # restart policy
docker run --memory=512m --cpus=1.0 image   # resource limits
```

## Containers — manage

```bash
docker ps                     # running
docker ps -a                  # all (incl. stopped)
docker logs -f web            # follow logs
docker logs --tail 100 web    # last 100 lines
docker exec -it web sh        # shell into running container
docker cp file web:/path      # copy into container
docker stats                  # live resource usage
docker top web                # processes inside
docker inspect web            # full metadata
docker stop web               # graceful stop (SIGTERM)
docker kill web               # force stop (SIGKILL)
docker restart web
docker start web
docker pause web / unpause web
docker rm web                 # remove stopped
docker rm -f web              # force remove
docker container prune        # remove all stopped
```

## Volumes

```bash
docker volume create my_vol
docker volume ls
docker volume inspect my_vol       # real host path
docker volume rm my_vol
docker volume prune                # remove unused
docker run -v my_vol:/data image           # named volume
docker run -v /host/path:/data image       # bind mount
docker run -v my_vol:/data:ro image        # read-only
docker run --tmpfs /cache image            # RAM-only
```

## Networking

```bash
docker network ls
docker network create app-net              # user-defined bridge
docker network create -d overlay ov-net    # overlay (Swarm)
docker network inspect app-net
docker network connect app-net web
docker network disconnect app-net web
docker network prune
docker run --network app-net --name web image   # attach at run
```

## Docker Compose (v2)

```bash
docker compose up -d          # start stack (detached)
docker compose up --build     # rebuild first
docker compose down           # stop + remove
docker compose down -v        # ...also remove volumes (deletes data!)
docker compose ps             # status
docker compose logs -f        # follow all logs
docker compose logs -f web    # one service
docker compose exec db psql   # run command in a service
docker compose build          # build only
docker compose restart web
docker compose up --scale web=3
```

## Swarm

```bash
docker swarm init --advertise-addr <IP>
docker swarm join --token <TOKEN> <IP>:2377
docker swarm leave --force
docker service create --name web --replicas 3 -p 80:80 nginx
docker service ls
docker service ps web                      # tasks + placement
docker service scale web=5
docker service update --image myapp:2.0 web
docker service rm web
docker node ls
docker stack deploy -c compose.yaml mystack
docker secret create db_pw ./pw.txt
```

## Buildx (multi-arch)

```bash
docker buildx create --name multi --use
docker buildx build --platform linux/amd64,linux/arm64 -t user/app:1.0 --push .
docker buildx ls
```

## Security & Scanning

```bash
docker scout cves myapp:1.0                # vulnerabilities
docker scout quickview myapp:1.0
trivy image myapp:1.0                       # (third-party)
docker run --read-only --cap-drop=ALL --security-opt=no-new-privileges app
```

## Cleanup

```bash
docker system prune               # stopped containers, unused nets, dangling images
docker system prune -a            # + all unused images
docker system prune -a --volumes  # + volumes (DANGEROUS)
docker container prune
docker image prune
docker volume prune
docker network prune
```

---

## Handy One-Liners

```bash
docker stop $(docker ps -q)          # stop all running
docker rm $(docker ps -aq)           # remove all containers
docker rmi $(docker images -q)       # remove all images
docker exec -it $(docker ps -q -f name=web) sh   # shell into "web"
docker logs -f --tail 50 web         # tail + follow
docker inspect -f '{{.NetworkSettings.IPAddress}}' web   # get container IP
```

---

## Signal / Lifecycle Quick Reference

| Command | Signal | Effect |
|---|---|---|
| `docker stop` | SIGTERM → SIGKILL | Graceful, then forced after grace period |
| `docker kill` | SIGKILL | Immediate |
| `docker restart` | stop + start | — |
| `docker pause` | SIGSTOP (cgroup freeze) | Freeze in RAM |

---

[◀ Back to README](../README.md)
