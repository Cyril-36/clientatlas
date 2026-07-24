FROM node:24-alpine AS dependencies
WORKDIR /app

COPY package.json package-lock.json ./
COPY apps/product-api/package.json apps/product-api/package.json
COPY packages/database/package.json packages/database/package.json
RUN npm ci

FROM dependencies AS builder
ARG NEXT_PUBLIC_AI_API_URL=http://127.0.0.1:8000
ARG NEXT_PUBLIC_DEMO_MODE=true
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ARG NEXT_PUBLIC_SUPABASE_URL
ENV NEXT_PUBLIC_AI_API_URL=$NEXT_PUBLIC_AI_API_URL
ENV NEXT_PUBLIC_DEMO_MODE=$NEXT_PUBLIC_DEMO_MODE
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY
ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL
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
