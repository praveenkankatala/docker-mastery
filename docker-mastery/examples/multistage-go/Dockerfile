# ---- Stage 1: build ----
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod .
COPY main.go .
# CGO_ENABLED=0 → fully static binary, runnable on a minimal base
RUN CGO_ENABLED=0 go build -o myapp .

# ---- Stage 2: runtime ----
FROM alpine:latest
WORKDIR /root/
COPY --from=builder /app/myapp .     # copy ONLY the binary
CMD ["./myapp"]
