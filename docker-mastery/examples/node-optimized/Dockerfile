# syntax=docker/dockerfile:1
FROM node:18-alpine

WORKDIR /usr/src/app

# 1. Copy dependency manifests FIRST so the install layer stays cached
COPY package*.json ./
RUN npm install --omit=dev && npm cache clean --force

# 2. Copy application source (changes most often → last)
COPY . .

# 3. Drop root
RUN addgroup -S app && adduser -S app -G app
USER app

# 4. Document port + liveness probe
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget -qO- http://localhost:3000/health || exit 1

# 5. Exec form → clean SIGTERM handling
CMD ["node", "index.js"]
