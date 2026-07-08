# Build the SvelteKit static frontend, the Fastify API, then run the API serving both.
# ---- web (static SPA) ----
FROM node:22-bookworm-slim AS web
WORKDIR /web
COPY web/package.json ./
RUN npm install
COPY web/ ./
# Google client id is baked into the SPA at build time.
ARG VITE_GOOGLE_CLIENT_ID
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID
RUN npm run build

# ---- api (compiled TS) ----
FROM node:22-bookworm-slim AS api
WORKDIR /api
COPY api/package.json api/package-lock.json ./
RUN npm ci
COPY api/ ./
RUN npm run build

# ---- runtime ----
FROM node:22-bookworm-slim
WORKDIR /app
ENV NODE_ENV=production
# Prod deps only; better-sqlite3 fetches its prebuilt native binary here.
COPY api/package.json api/package-lock.json ./
RUN npm ci --omit=dev
COPY --from=api /api/dist ./dist
COPY --from=web /web/build ./web/build
ENV WEB_DIST=/app/web/build \
    DATABASE=/data/timesheet.sqlite3 \
    HOST=0.0.0.0 \
    PORT=8000
EXPOSE 8000
CMD ["node", "dist/index.js"]
