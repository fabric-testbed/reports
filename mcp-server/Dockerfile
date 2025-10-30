# ---------- Stage 1: build TypeScript ----------
FROM node:22-bookworm-slim AS builder
WORKDIR /app

# Install all deps (dev + prod) for build
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source and config
COPY tsconfig.json ./
COPY src ./src

# Compile TypeScript -> dist/
RUN npx tsc --pretty false

# ---------- Stage 2: runtime ----------
FROM node:22-bookworm-slim AS runtime
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=4000
# Adjust this if your health path differs
ENV HEALTHCHECK_PATH=/mcp

# Create non-root user
RUN useradd -m -u 10001 nodeuser

# Install only production deps
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev

# Copy compiled JS from builder
COPY --from=builder /app/dist ./dist

# Expose port for HTTP
EXPOSE 4000

# Healthcheck – optional
HEALTHCHECK --interval=20s --timeout=3s --retries=10 CMD \
  wget -qO- "http://127.0.0.1:${PORT}${HEALTHCHECK_PATH}" >/dev/null 2>&1 || exit 1

# Drop privileges
USER nodeuser

# Start the compiled server
CMD ["node", "dist/index.js"]
