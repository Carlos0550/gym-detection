# syntax=docker/dockerfile:1.7

# ============================================================
# Frontend: Next.js 15 (App Router) - dev mode con hot reload
# ============================================================
FROM node:20-alpine

# libc6-compat: necesario para que algunas deps nativas (sharp, etc.) funcionen en alpine
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Cache de deps: copiamos solo manifests primero
COPY package.json ./
# Si vas a usar lockfile en el futuro, copiar también:
# COPY package-lock.json* ./

# Instalación. Si hay package-lock.json se usa npm ci, si no, npm install.
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Código
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=development

EXPOSE 3000

# Permitir conexiones desde el host (no solo localhost)
ENV HOSTNAME=0.0.0.0

CMD ["npm", "run", "dev"]
