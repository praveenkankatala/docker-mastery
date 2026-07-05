# multistage-go · Multi-Stage Build Example

Same program, two Dockerfiles — one naive, one multi-stage — to show the size difference.

## Build both and compare

```bash
docker build -t go-fat  -f Dockerfile.naive .
docker build -t go-slim -f Dockerfile .
docker images | grep -E "go-(fat|slim)"
docker run --rm go-slim
```

`go-fat` ships the entire Go toolchain. `go-slim` copies only the compiled
static binary into a bare Alpine image — typically an order of magnitude smaller.

## Going even smaller

Swap the runtime stage's `FROM alpine:latest` for `FROM scratch` (empty image).
Because `CGO_ENABLED=0` produces a static binary, it needs no OS at all.
