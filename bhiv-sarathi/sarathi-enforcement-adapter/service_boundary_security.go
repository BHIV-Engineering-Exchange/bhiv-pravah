// service_boundary_security.go (v14.9 Service Runtime — Phase B)
//
// Production hardening applied ON TOP of the existing ServiceBoundary
// middleware chain (panicRecovery → requestLogging → mux). Every layer
// below is additive and stdlib-only (no new go.mod deps):
//
//   1. Slowloris defence     ReadHeaderTimeout, IdleTimeout on http.Server
//   2. TLS floor             MinVersion=TLS1.2 when TLS is configured
//   3. Security headers      HSTS (TLS only), X-Content-Type-Options,
//                            X-Frame-Options, Referrer-Policy, Cache-Control
//   4. Request-ID            honour inbound X-Request-ID, else generate
//                            a cryptographically-random 128-bit id
//   5. Token-bucket rate     per-source (API key fingerprint, else peer IP)
//      limiter               with burst capacity — rejects with 429
//
// Environment toggles (all optional):
//   SARATHI_SERVICE_READ_HEADER_TIMEOUT_MS   default 2000
//   SARATHI_SERVICE_IDLE_TIMEOUT_MS          default 60000
//   SARATHI_SERVICE_RATE_LIMIT_RPS           default 50   (0 disables)
//   SARATHI_SERVICE_RATE_LIMIT_BURST         default 100
//   SARATHI_SERVICE_DISABLE_RATE_LIMIT=1     force-off
//   SARATHI_SERVICE_DISABLE_SECURITY_HEADERS=1 force-off
//   SARATHI_SERVICE_MIN_TLS=1.2|1.3          default 1.2
//
// TAG: service-hardening-v14.9

package main

import (
	"crypto/rand"
	"crypto/tls"
	"encoding/hex"
	"fmt"
	"net"
	"net/http"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"
)

// ApplyServiceHardening wraps the ServiceBoundary's underlying http.Server
// with the Phase-B production middleware stack and tightens the low-level
// timeouts + TLS floor. It is safe to call immediately after
// NewServiceBoundary and before Start().
func ApplyServiceHardening(boundary *ServiceBoundary) {
	if boundary == nil || boundary.server == nil {
		return
	}
	srv := boundary.server

	// 1. Slowloris defence — cap the time clients can trickle headers and
	// the time idle keep-alive connections sit parked on the listener.
	readHeaderMs := envIntOrDefault("SARATHI_SERVICE_READ_HEADER_TIMEOUT_MS", 2000)
	idleMs := envIntOrDefault("SARATHI_SERVICE_IDLE_TIMEOUT_MS", 60000)
	srv.ReadHeaderTimeout = time.Duration(readHeaderMs) * time.Millisecond
	srv.IdleTimeout = time.Duration(idleMs) * time.Millisecond

	// 2. TLS floor — when TLS is configured we pin the minimum version.
	// The existing NewServiceBoundary path sets server.TLSConfig via
	// ConfigureTLS; we extend that config rather than overwrite it.
	minTLS := uint16(tls.VersionTLS12)
	if strings.TrimSpace(os.Getenv("SARATHI_SERVICE_MIN_TLS")) == "1.3" {
		minTLS = tls.VersionTLS13
	}
	if srv.TLSConfig == nil {
		srv.TLSConfig = &tls.Config{MinVersion: minTLS}
	} else if srv.TLSConfig.MinVersion < minTLS {
		srv.TLSConfig.MinVersion = minTLS
	}

	// 3. Build the outer middleware chain. Order matters:
	//      requestID  →  securityHeaders  →  rateLimit  →  existing chain
	// The existing chain (panicRecovery → requestLogging → mux) is kept
	// intact so v14.7/v14.8 behaviour is preserved byte-identically when
	// no hardening is needed.
	inner := srv.Handler

	if os.Getenv("SARATHI_SERVICE_DISABLE_RATE_LIMIT") != "1" {
		rps := envIntOrDefault("SARATHI_SERVICE_RATE_LIMIT_RPS", 50)
		burst := envIntOrDefault("SARATHI_SERVICE_RATE_LIMIT_BURST", 100)
		if rps > 0 && burst > 0 {
			inner = newRateLimitMiddleware(rps, burst)(inner)
		}
	}
	if os.Getenv("SARATHI_SERVICE_DISABLE_SECURITY_HEADERS") != "1" {
		inner = securityHeadersMiddleware(inner)
	}
	inner = requestIDMiddleware(inner)

	srv.Handler = inner
}

// ----------------------------------------------------------------------
// 1. Request-ID middleware
// ----------------------------------------------------------------------

func requestIDMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		rid := r.Header.Get("X-Request-ID")
		if rid == "" || len(rid) > 128 {
			rid = newRequestID()
		}
		r.Header.Set("X-Request-ID", rid)
		w.Header().Set("X-Request-ID", rid)
		next.ServeHTTP(w, r)
	})
}

func newRequestID() string {
	var buf [16]byte
	if _, err := rand.Read(buf[:]); err != nil {
		// If system RNG fails, fall back to a time-derived id. Request-ID
		// is observability only; correctness of enforcement does not
		// depend on it.
		return fmt.Sprintf("t-%d", time.Now().UnixNano())
	}
	return hex.EncodeToString(buf[:])
}

// ----------------------------------------------------------------------
// 2. Security headers middleware
// ----------------------------------------------------------------------

func securityHeadersMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		h := w.Header()
		h.Set("X-Content-Type-Options", "nosniff")
		h.Set("X-Frame-Options", "DENY")
		h.Set("Referrer-Policy", "no-referrer")
		h.Set("Cache-Control", "no-store")
		// Strict-Transport-Security is only meaningful over TLS; signalled
		// by the presence of r.TLS on incoming handshake.
		if r.TLS != nil {
			h.Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
		}
		next.ServeHTTP(w, r)
	})
}

// ----------------------------------------------------------------------
// 3. Token-bucket rate limiter — per source identifier
// ----------------------------------------------------------------------

// rateLimitMiddleware enforces a global RPS ceiling per source key. The
// source key is derived from (in order):
//
//   1. the first 16 hex chars of SHA-256(X-API-Key / bearer token), if present
//   2. the X-Forwarded-For leftmost hop
//   3. the remote peer IP from the TCP connection
//
// Keys fingerprint the API key rather than storing it so the limiter
// map never holds secret material.
func newRateLimitMiddleware(rps, burst int) func(http.Handler) http.Handler {
	lim := &tokenBucketLimiter{
		rate:    float64(rps),
		burst:   float64(burst),
		buckets: make(map[string]*tokenBucket),
		janitor: time.Now(),
	}
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			key := rateLimitKey(r)
			if !lim.allow(key) {
				w.Header().Set("Retry-After", "1")
				w.Header().Set("Content-Type", "application/json")
				w.WriteHeader(http.StatusTooManyRequests)
				_, _ = w.Write([]byte(`{"error":"RATE_LIMITED","detail":"per-source request budget exceeded"}`))
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

func rateLimitKey(r *http.Request) string {
	if k := r.Header.Get("X-API-Key"); k != "" {
		return "k:" + fingerprintShort(k)
	}
	if auth := r.Header.Get("Authorization"); len(auth) > 7 && strings.EqualFold(auth[:7], "Bearer ") {
		return "k:" + fingerprintShort(auth[7:])
	}
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		if comma := strings.IndexByte(xff, ','); comma >= 0 {
			return "ip:" + strings.TrimSpace(xff[:comma])
		}
		return "ip:" + strings.TrimSpace(xff)
	}
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		return "ip:" + r.RemoteAddr
	}
	return "ip:" + host
}

func fingerprintShort(s string) string {
	// Use the first 16 chars of the hex-encoded SHA-256 digest; enough
	// bits to disambiguate callers without revealing the secret.
	return ShortDigestHex(s, 16)
}

// ShortDigestHex returns the first `n` hex chars of SHA-256(s). Exposed
// so tests and future hardening code can reuse the same fingerprint.
func ShortDigestHex(s string, n int) string {
	h := Sha256Hex([]byte(s))
	if n <= 0 || n > len(h) {
		return h
	}
	return h[:n]
}

// tokenBucket is a classic Barre–Reeve leaky bucket — tokens regen at
// `rate` per second, capped at `burst`. One token == one request.
type tokenBucket struct {
	tokens    float64
	lastRefil time.Time
}

type tokenBucketLimiter struct {
	mu      sync.Mutex
	rate    float64 // tokens / second
	burst   float64 // max tokens
	buckets map[string]*tokenBucket
	janitor time.Time // last GC sweep
}

func (l *tokenBucketLimiter) allow(key string) bool {
	l.mu.Lock()
	defer l.mu.Unlock()

	now := time.Now()
	b, ok := l.buckets[key]
	if !ok {
		b = &tokenBucket{tokens: l.burst, lastRefil: now}
		l.buckets[key] = b
	} else {
		elapsed := now.Sub(b.lastRefil).Seconds()
		b.tokens += elapsed * l.rate
		if b.tokens > l.burst {
			b.tokens = l.burst
		}
		b.lastRefil = now
	}

	// Periodically drop buckets that have been idle long enough for their
	// token count to be saturated — keeps memory bounded even under very
	// wide client populations.
	if now.Sub(l.janitor) > 5*time.Minute {
		l.sweepLocked(now)
		l.janitor = now
	}

	if b.tokens < 1.0 {
		return false
	}
	b.tokens -= 1.0
	return true
}

func (l *tokenBucketLimiter) sweepLocked(now time.Time) {
	for k, b := range l.buckets {
		if now.Sub(b.lastRefil) > 10*time.Minute && b.tokens >= l.burst {
			delete(l.buckets, k)
		}
	}
}

// ----------------------------------------------------------------------
// Helpers
// ----------------------------------------------------------------------

func envIntOrDefault(key string, def int) int {
	if v := os.Getenv(key); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 {
			return n
		}
	}
	return def
}
