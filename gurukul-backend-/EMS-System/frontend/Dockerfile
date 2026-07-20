# Build stage - run with context at repo root so prana-core is available
FROM node:20-alpine AS build
# prana-core is imported by ems_prana.js as ../../prana-core (from frontend = repo root)
COPY prana-core /prana-core
COPY ["EMS-System/frontend", "/app"]
WORKDIR /app
RUN npm install
ARG VITE_API_URL=http://localhost:8000
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
EXPOSE 3001
CMD ["serve", "-s", "dist", "-l", "3001"]

