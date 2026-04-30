# syntax=docker/dockerfile:1.7
# Multi-stage build for the Praxis Next.js operator terminal.

FROM node:20-alpine AS deps
# bufferutil + utf-8-validate (transitive via wagmi/viem ws) need node-gyp.
# Keep the build deps in a virtual package and remove after install so the
# layer doesn't carry compilers into the cached image. First build takes
# ~10-15 minutes; subsequent builds reuse the cached layer.
RUN apk add --no-cache --virtual .build-deps python3 make g++ libc-dev
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund \
    && apk del .build-deps

FROM node:20-alpine AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

RUN addgroup -S praxis && adduser -S praxis -G praxis
COPY --from=builder --chown=praxis:praxis /app/.next/standalone ./
COPY --from=builder --chown=praxis:praxis /app/.next/static ./.next/static
COPY --from=builder --chown=praxis:praxis /app/public ./public
USER praxis

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD wget -q -O - http://localhost:3000 >/dev/null 2>&1 || exit 1

CMD ["node", "server.js"]
