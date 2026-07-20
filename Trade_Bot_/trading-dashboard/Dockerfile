FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Accept build-time args for Vite env vars (passed via --build-arg in CI/CD)
ARG VITE_API_BASE_BACKEND_URL
ARG VITE_PREDICTION_API_URL
ARG VITE_ENABLE_AUTH=false
ENV VITE_API_BASE_BACKEND_URL=$VITE_API_BASE_BACKEND_URL
ENV VITE_PREDICTION_API_URL=$VITE_PREDICTION_API_URL
ENV VITE_ENABLE_AUTH=$VITE_ENABLE_AUTH

RUN npm run build

FROM node:20-alpine

WORKDIR /app

# install only a lightweight static server
RUN npm install -g serve

COPY --from=builder /app/dist ./dist

RUN adduser --disabled-password --gecos "" frontend

RUN mkdir -p /app/data/cache && \
    chown -R frontend:frontend /app

USER frontend

EXPOSE 5173

CMD ["serve", "-s", "dist", "-l", "5173"]
