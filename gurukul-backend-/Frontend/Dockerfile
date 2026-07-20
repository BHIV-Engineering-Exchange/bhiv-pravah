# Build stage - run with context at repo root so prana-core is available
FROM node:20-alpine AS build
# prana-core is imported by gurukul_prana.js and src/utils as ../prana-core (from Frontend = repo root)
COPY prana-core /prana-core
COPY Frontend /app
WORKDIR /app
RUN npm ci
ARG VITE_API_URL=http://localhost:3000
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Serve stage
FROM node:20-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=build /app/dist ./dist
RUN adduser --disabled-password --gecos "" frontend && \
    chown -R frontend:frontend /app
USER frontend
EXPOSE 5174
CMD ["serve", "-s", "dist", "-l", "5174"]

