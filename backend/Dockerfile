# Étape 1 : Construction
# Node 22 : version exigée par "engines" dans package.json
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npx prisma generate
RUN npm run build

# Étape 2 : Production
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY package*.json ./
# Dépendances de production uniquement, puis suppression de npm/npx/corepack/yarn :
# l'API n'en a pas besoin pour tourner (CMD = node), et les dépendances embarquées
# par npm (ex. tar) remontaient des vulnérabilités CRITICAL dans le scan Trivy.
RUN npm ci --omit=dev \
 && npm cache clean --force \
 && rm -rf /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/corepack \
           /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack \
           /opt/yarn-* /usr/local/bin/yarn /usr/local/bin/yarnpkg

# Copie des fichiers nécessaires depuis le builder
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/prisma ./prisma
COPY --from=builder /app/node_modules/.prisma ./node_modules/.prisma

# Utilisateur non-root (fourni par l'image node)
USER node

EXPOSE 4000
CMD ["node", "dist/server.js"]
