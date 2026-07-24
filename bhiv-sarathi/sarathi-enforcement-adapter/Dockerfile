# Sarathi Enforcement Adapter — Docker Build
# Multi-stage build for minimal production image
#
# Usage:
#   docker build -t sarathi-enforcement-adapter .
#   docker run --rm sarathi-enforcement-adapter
#
# With custom API keys (production):
#   docker run --rm \
#     -e SARATHI_CALLER_KEY_CORE=your-core-key \
#     -e SARATHI_CALLER_KEY_INTENT=your-intent-key \
#     -e SARATHI_CALLER_KEY_INSIGHTFLOW=your-insight-key \
#     -e SARATHI_CALLER_KEY_BUCKET=your-bucket-key \
#     -e SARATHI_CALLER_KEY_ADMIN=your-admin-key \
#     sarathi-enforcement-adapter

# Stage 1: Build
FROM golang:1.24-alpine AS builder

WORKDIR /app

# Copy dependency files first (cache layer)
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY *.go ./
COPY policies/ ./policies/
COPY registry_config.json ./

# Build static binary
RUN CGO_ENABLED=0 GOOS=linux go build -o sarathi-enforcement-adapter .

# Stage 2: Runtime (minimal image)
FROM alpine:3.19

RUN apk --no-cache add ca-certificates

WORKDIR /app

# Copy binary and required files
COPY --from=builder /app/sarathi-enforcement-adapter .
COPY --from=builder /app/policies/ ./policies/
COPY --from=builder /app/registry_config.json ./

# Non-root user for security
RUN adduser -D -u 1000 sarathi
USER sarathi

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD ["/app/sarathi-enforcement-adapter", "--health"] || exit 1

EXPOSE 8443

ENTRYPOINT ["/app/sarathi-enforcement-adapter"]
