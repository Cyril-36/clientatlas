FROM node:24-alpine AS dependencies
WORKDIR /app

COPY package.json package-lock.json ./
COPY apps/product-api/package.json apps/product-api/package.json
COPY packages/database/package.json packages/database/package.json
RUN npm ci

FROM dependencies AS builder
COPY tsconfig.base.json ./
COPY apps/product-api apps/product-api
COPY packages/database packages/database
RUN npm run build --workspace @clientatlas/product-api

FROM node:24-alpine AS runner
ENV HOSTNAME=0.0.0.0
ENV NODE_ENV=production
ENV PORT=3000
WORKDIR /app

RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

COPY --from=builder --chown=nextjs:nodejs \
  /app/apps/product-api/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs \
  /app/apps/product-api/.next/static \
  ./apps/product-api/.next/static

USER nextjs
EXPOSE 3000
CMD ["node", "apps/product-api/server.js"]

