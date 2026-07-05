# 05 · Storage & Volumes

[◀ Containers](./04-containers.md) | [Back to README](../README.md) | [Next: Networking ▶](./06-networking.md)

---

Containers are **ephemeral** — delete one and everything written to its writable layer is gone. To keep or share data, you store it *outside* the container.

---

## 1. The Writable Layer (temporary)

Every container has a thin read-write layer on top of the read-only image. All in-container changes land here, managed by a **storage driver** (usually `overlay2`) using Copy-on-Write. It's fine for scratch data, but it dies with the container and is slower than direct disk access.

---

## 2. The Three Mount Types

```
        ┌──────────── CONTAINER ────────────┐
        │  /app/data   /app/code   /cache   │
        └─────┬───────────┬──────────┬──────┘
              │           │          │
       ┌──────▼─────┐ ┌───▼──────┐ ┌─▼─────────┐
       │  VOLUME    │ │  BIND    │ │  tmpfs    │
       │ Docker-    │ │  MOUNT   │ │  (RAM,    │
       │ managed    │ │ host     │ │  never    │
       │/var/lib/   │ │ path     │ │  on disk) │
       │docker/vol/ │ │          │ │           │
       └────────────┘ └──────────┘ └───────────┘
```

### A. Volumes — the preferred way

Docker-managed storage kept under `/var/lib/docker/volumes/`. Portable, easy to back up, works with drivers (cloud/NFS), safe to share between containers.

```bash
docker run -d -v my_data:/app/data nginx
```

**Best for:** databases, production data, anything that must survive.

### B. Bind Mounts — map a host path directly

Maps a specific host directory/file into the container. Great for development (edit code on your laptop, container sees it instantly), but ties you to the host's exact path, so it's less portable.

```bash
docker run -d -v /home/user/project:/app nginx
```

**Best for:** local dev, live code reload, injecting config files.

### C. tmpfs Mounts — RAM only

Data lives in host memory, never touches disk, and vanishes when the container stops.

```bash
docker run -d --tmpfs /app/cache nginx
```

**Best for:** secrets you don't want on disk, high-speed ephemeral cache.

### Comparison

| Feature | Volume | Bind Mount | tmpfs |
|---|---|---|---|
| Managed by | Docker | You (host paths) | OS memory |
| Portability | High | Low | Medium |
| Performance | High | High | Fastest (RAM) |
| Survives container delete | Yes | Yes | No (wiped on stop) |
| Typical use | Databases, app data | Dev code / config | Secrets, cache |

---

## 3. Volumes in Depth

### Named vs Anonymous

- **Named** (`-v my_db:/data`) — you give it a name; it persists independently of any container. Use these.
- **Anonymous** (`-v /data`) — Docker assigns a random hash name; easy to lose track of and end up "dangling."

### `-v` vs `--mount`

Two syntaxes attach a volume. `--mount` is verbose but explicit and harder to get wrong (recommended for scripts/prod).

```bash
# Short form
docker run -d -v my_db_data:/var/lib/mysql mysql:8

# Explicit form (recommended)
docker run -d \
  --mount source=my_db_data,target=/var/lib/mysql \
  mysql:8
```

### Read-only mounts

Give a container access without letting it modify (e.g. config):

```bash
docker run -v my_config:/app/config:ro my-app
# or
docker run --mount source=my_config,target=/app/config,readonly my-app
```

### Pre-populating a volume

If you mount an **empty** named volume onto a container directory that already contains files (e.g. `/usr/share/nginx/html`), Docker copies those files *into* the volume on first use. So you don't start empty. (This only happens with volumes on an empty target, not bind mounts.)

### Managing volumes

```bash
docker volume create my_data       # create
docker volume ls                   # list
docker volume inspect my_data      # see the real host path + metadata
docker volume rm my_data           # remove (must be unused)
docker volume prune                # remove ALL unused volumes (careful!)
```

---

## 4. Storage Drivers (under the hood)

Volumes and bind mounts bypass the container's internal storage for speed. The container's *own* filesystem is handled by a **storage driver**, most commonly **`overlay2`**, using **Copy-on-Write**:

1. Read a file → served straight from the read-only image layer.
2. Modify a file → driver copies it up to the writable layer first, then edits the copy.

This keeps the underlying image untouched and lets many containers share the same base layers.

---

## 5. Backing Up a Volume

A common real-world task — dump a named volume to a tarball:

```bash
docker run --rm \
  -v my_db_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/db-backup.tar.gz -C /data .
```

Restore:

```bash
docker run --rm \
  -v my_db_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/db-backup.tar.gz -C /data
```

---

## 🧪 Lab

See [labs/labs.md → Lab 5](../labs/labs.md#lab-5--persist-data-with-a-volume). Write data with no volume and lose it, then repeat with a named volume and prove it survives across a full container recreate.

---

## ⚠️ Common Pitfalls

- **Storing DB data in the writable layer.** One `docker rm` and your database is gone. Always mount a volume.
- **`docker volume prune` on shared hosts.** Deletes every unused volume — including data you meant to keep.
- **Bind mount path assumptions.** A Windows/Mac host path won't exist on a Linux server; volumes are portable, bind mounts aren't.
- **Expecting bind mounts to pre-populate.** Only *named volumes* on an empty target copy the image's existing files in; a bind mount *hides* whatever was there.
- **Anonymous volumes piling up.** They accumulate as dangling volumes. Prefer named volumes.

---

## ✅ Knowledge Check

1. Which mount type should hold a production database, and why?
2. What's the difference between a named and an anonymous volume?
3. When would you use a bind mount over a volume?
4. What does Copy-on-Write do when a container edits a file from the image?

<details>
<summary>Answers</summary>

1. A named **volume** — Docker-managed, portable, easy to back up, survives container deletion.
2. Named volumes have a stable name you control and persist independently; anonymous volumes get a random hash and are easily lost/dangling.
3. Local development, to live-edit source or inject host config into the container.
4. Copies the file from the read-only image layer up into the writable layer, then edits the copy — the image stays unchanged.
</details>

---

[◀ Containers](./04-containers.md) | [Back to README](../README.md) | [Next: Networking ▶](./06-networking.md)
