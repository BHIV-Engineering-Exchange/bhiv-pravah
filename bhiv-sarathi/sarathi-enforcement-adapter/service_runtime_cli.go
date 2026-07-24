// service_runtime_cli.go (v14.9 Service Runtime)
//
// Long-lived HTTP service runtime — the production-grade entry point that
// exposes the Gated Bridge to BHIV Core / InsightFlow / Bucket (and any
// authorised caller) over real network TCP. Unlike every other CLI mode,
// `--service` does NOT run a batch harness and exit; it boots the full
// enforcement pipeline, binds the ServiceBoundary HTTP server, and blocks
// until SIGINT/SIGTERM.
//
// Dispatch ordering: parsed BEFORE v14.8 in enforcement_adapter_main.go so
// a bare `--service` invocation owns the process unconditionally.
//
// Environment variables (all optional, sensible defaults):
//   SARATHI_SERVICE_ADDR                   Listen address (default 127.0.0.1:8443)
//   SARATHI_SERVICE_READ_TIMEOUT_MS        http.Server.ReadTimeout
//   SARATHI_SERVICE_WRITE_TIMEOUT_MS       http.Server.WriteTimeout
//   SARATHI_SERVICE_MAX_BODY_BYTES         Body size cap (default 1 MiB)
//   SARATHI_SERVICE_SHUTDOWN_TIMEOUT_S     Graceful shutdown deadline (default 30)
//   SARATHI_TLS_CERT_PATH, SARATHI_TLS_KEY_PATH  Enables HTTPS when both set
//   SARATHI_CALLER_KEY_<SYSTEM>            Per-caller API keys (see LoadSecureConfig)
//   SARATHI_SERVICE_REQUIRE_TLS=1          Abort bootstrap if TLS is not configured
//   SARATHI_SERVICE_REQUIRE_NONDEFAULT_KEYS=1  Abort if any default API key is in use
//
// TAG: service-runtime-v14.9

package main

import (
	"context"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"syscall"
	"time"
)

// v14.9 service runtime flags.
const (
	ServiceFlag         = "--service"
	ServiceLiveDemoFlag = "--service-live-demo"
)

// ServiceRuntimeMode is the parsed service-runtime invocation.
type ServiceRuntimeMode struct {
	Name string // "service" | "service-live-demo"
	Ok   bool
}

// ParseServiceRuntimeArgs scans argv for `--service` and `--service-live-demo`.
// Bare flags; configuration is supplied via environment variables.
func ParseServiceRuntimeArgs(argv []string) ServiceRuntimeMode {
	for i := 1; i < len(argv); i++ {
		switch argv[i] {
		case ServiceFlag:
			return ServiceRuntimeMode{Name: "service", Ok: true}
		case ServiceLiveDemoFlag:
			return ServiceRuntimeMode{Name: "service-live-demo", Ok: true}
		}
	}
	return ServiceRuntimeMode{Ok: false}
}

// preflightRemoteTrustURL is the v15.1 boot-time gate for
// SARATHI_TRUST_REMOTE_URL. Returns ("", "") on success; on failure returns
// the error code constant and a human-readable detail. Two failure modes:
//
//  1. Plain http:// scheme in production — refused with
//     CodeTrustRemoteURLInsecure. Aligns with JWKS 2026 best practices
//     (devtoolkit.cloud / workos.com): never fetch trust bundles over
//     plain HTTP because a MITM substituting a different bundle could
//     forge accepted tokens.
//  2. URL unreachable on 5 s GET — refused with
//     CodeTrustRemoteURLUnreachable. Avoids the silent "service binds, then
//     every request 502s" failure mode the v15.0 path otherwise has.
//
// Probe is a HEAD then GET fallback against the URL itself (NOT a /health
// suffix — the registry contract does not mandate a /health route). A 2xx
// or 3xx response is accepted; 4xx/5xx + transport errors are refused.
func preflightRemoteTrustURL(remoteURL string) (code, detail string) {
	parsed, err := url.Parse(remoteURL)
	if err != nil {
		return CodeTrustRemoteURLInsecure,
			fmt.Sprintf("SARATHI_TRUST_REMOTE_URL is not a valid URL: %v", err)
	}
	if !strings.EqualFold(parsed.Scheme, "https") {
		return CodeTrustRemoteURLInsecure,
			fmt.Sprintf("SARATHI_TRUST_REMOTE_URL must use https:// in production (got %q). MITM substitution of a plain-http registry would forge accepted evaluator identities.", parsed.Scheme)
	}

	client := &http.Client{Timeout: 5 * time.Second}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	doProbe := func(method string) (int, error) {
		req, err := http.NewRequestWithContext(ctx, method, remoteURL, nil)
		if err != nil {
			return 0, err
		}
		if k := os.Getenv("SARATHI_TRUST_REMOTE_KEY"); k != "" {
			req.Header.Set("Authorization", "Bearer "+k)
		}
		req.Header.Set("X-Sarathi-Component", "PreflightRemoteTrustURL")
		resp, err := client.Do(req)
		if err != nil {
			return 0, err
		}
		defer resp.Body.Close()
		return resp.StatusCode, nil
	}

	status, err := doProbe(http.MethodHead)
	if err != nil || status >= 400 {
		// HEAD may legitimately be unsupported — fall back to GET.
		status, err = doProbe(http.MethodGet)
	}
	if err != nil {
		return CodeTrustRemoteURLUnreachable,
			fmt.Sprintf("SARATHI_TRUST_REMOTE_URL probe failed: %v", err)
	}
	if status >= 400 {
		return CodeTrustRemoteURLUnreachable,
			fmt.Sprintf("SARATHI_TRUST_REMOTE_URL probe returned HTTP %d (need 2xx/3xx)", status)
	}
	return "", ""
}

// RunServiceRuntimeMode dispatches to the selected runtime entry point.
func RunServiceRuntimeMode(mode ServiceRuntimeMode) int {
	switch mode.Name {
	case "service":
		return RunServiceRuntime()
	case "service-live-demo":
		return RunServiceLiveDemo()
	default:
		fmt.Fprintf(os.Stderr, "unknown service runtime mode: %s\n", mode.Name)
		return 2
	}
}

// bootstrapServiceBoundary builds the full enforcement stack and the
// hardened ServiceBoundary, without calling Start(). The returned
// boundary is ready to be handed to Start() or to an in-process
// `net/http/httptest` client. Exported helper used by
// RunServiceRuntime + RunServiceLiveDemo to guarantee they exercise the
// same bootstrap path.
func bootstrapServiceBoundary(listenAddr string) (*ServiceBoundary, func(), error) {
	policiesDir, configPath, err := detectPaths()
	if err != nil {
		return nil, nil, fmt.Errorf("detectPaths: %w", err)
	}
	pipeline, err := NewSarathiEnforcementPipeline(policiesDir, configPath)
	if err != nil {
		return nil, nil, fmt.Errorf("pipeline init: %w", err)
	}
	if webhookURL := os.Getenv("SARATHI_WEBHOOK_URL"); webhookURL != "" {
		pipeline.EnableWebhookExecution(webhookURL)
	}
	auditSink := NewInMemoryAuditSink()
	service, err := NewSaarthiService(pipeline, auditSink)
	if err != nil {
		return nil, nil, fmt.Errorf("service init: %w", err)
	}
	router := NewMultiSystemRouter(auditSink)
	bridge, err := NewGatedBridge(service, router, DefaultBridgeConfig())
	if err != nil {
		return nil, nil, fmt.Errorf("bridge init: %w", err)
	}

	boundaryCfg := DefaultServiceBoundaryConfig()
	boundaryCfg.ListenAddr = listenAddr
	if v, err := strconv.Atoi(os.Getenv("SARATHI_SERVICE_READ_TIMEOUT_MS")); err == nil && v > 0 {
		boundaryCfg.ReadTimeoutMs = v
	}
	if v, err := strconv.Atoi(os.Getenv("SARATHI_SERVICE_WRITE_TIMEOUT_MS")); err == nil && v > 0 {
		boundaryCfg.WriteTimeoutMs = v
	}
	if v, err := strconv.ParseInt(os.Getenv("SARATHI_SERVICE_MAX_BODY_BYTES"), 10, 64); err == nil && v > 0 {
		boundaryCfg.MaxRequestBodyBytes = v
	}

	boundary, err := NewServiceBoundary(bridge, boundaryCfg)
	if err != nil {
		return nil, nil, fmt.Errorf("ServiceBoundary init: %w", err)
	}
	ApplyServiceHardening(boundary)

	// v15.0 Sovereign Identity Closure: mount inbound auth middleware iff
	// SARATHI_INBOUND_AUTH is set to "optional" or "required". When unset
	// (Stage A default), NewInboundAuthMiddleware returns (nil, nil) and
	// SetInboundAuth is a no-op — v14.9 path stays byte-identical.
	inboundCfg := DefaultInboundAuthConfig(pipeline.TrustConsumer)
	inboundMW, ierr := NewInboundAuthMiddleware(inboundCfg)
	if ierr != nil {
		return nil, nil, fmt.Errorf("inbound auth init: %w", ierr)
	}
	boundary.SetInboundAuth(inboundMW)
	if inboundMW != nil {
		fmt.Printf("  [v15.0] inbound-auth ACTIVE (mode=%s, skew=%s, nonce_window=%s)\n",
			inboundMW.Mode(), inboundCfg.MaxSkew, inboundCfg.NonceWindow)
	} else {
		fmt.Println("  [v15.0] inbound-auth OFF (default — set SARATHI_INBOUND_AUTH=optional|required to enable)")
	}

	// v15.6 JWT Authority. Loads from env (SARATHI_JWT_AUTHORITY_PRIV_PATH
	// etc.); production gates enforce that ephemeral / insecure
	// configurations refuse to start.
	jwtAuth, jwtErr := LoadJWTAuthorityFromEnv()
	if jwtErr != nil {
		return nil, nil, fmt.Errorf("jwt authority init: %w", jwtErr)
	}
	if jwtAuth != nil {
		if gateErr := EnforceJWTAuthorityProductionGates(jwtAuth); gateErr != nil {
			return nil, nil, gateErr
		}
		boundary.SetJWTAuthority(jwtAuth)
		service.SetJWTAuthority(jwtAuth)
		if jwtAuth.IsEphemeral() {
			fmt.Printf("  [v15.6] JWT-authority ACTIVE — EPHEMERAL KEY kid=%s (set SARATHI_JWT_AUTHORITY_PRIV_PATH to persist; Bridge JWKS cache will rotate on restart)\n",
				jwtAuth.CurrentKid())
		} else {
			fmt.Printf("  [v15.6] JWT-authority ACTIVE kid=%s issuer=%q ttl=%s\n",
				jwtAuth.CurrentKid(), jwtAuth.Issuer(), jwtAuth.TokenTTL())
		}
		if jwtAuth.IntrospectionEnabled() {
			fmt.Println("  [v15.6] introspection endpoint ENABLED (POST " + TokenIntrospectPath + ")")
		} else {
			fmt.Println("  [v15.6] introspection endpoint DISABLED (set SARATHI_JWT_INTROSPECTION_API_KEY to enable)")
		}
	} else {
		fmt.Println("  [v15.6] JWT-authority OFF (no signer loaded — Bridge JWT path inactive)")
	}

	// v15.6 Bridge-only surface gate (must run AFTER JWT authority load so
	// the production gate can refuse ephemeral keys in bridge-only mode).
	if BridgeOnlyModeFromEnv() {
		if strings.EqualFold(os.Getenv("SARATHI_ENV"), "production") &&
			(jwtAuth == nil || jwtAuth.IsEphemeral()) {
			return nil, nil, fmt.Errorf(
				"FATAL: ERR_JWT_AUTHORITY_EPHEMERAL_IN_BRIDGE_MODE — SARATHI_BRIDGE_ONLY_MODE=1 + SARATHI_ENV=production requires a persistent SARATHI_JWT_AUTHORITY_PRIV_PATH")
		}
		boundary.SetBridgeOnlyMode(true)
		fmt.Println("  [v15.6] BRIDGE-ONLY MODE ENABLED — /v1/enforce + /v1/ingest-decision + /v1/bridge/info return 404")
	}

	cleanup := func() {
		if inboundMW != nil {
			_ = inboundMW.Close()
		}
		_ = boundary.GracefulShutdown(5 * time.Second)
	}
	return boundary, cleanup, nil
}

// EnforceJWTAuthorityProductionGates refuses to start the service when
// SARATHI_ENV=production and any of the v15.6 production constraints are
// unmet. Returns nil in dev mode.
//
// Constraints:
//   * SARATHI_JWT_AUTHORITY_PRIV_PATH must be set + readable
//     (ephemeral keys would force Bridge to refetch JWKS every restart).
//   * SARATHI_TOKEN_ISSUER must be a non-empty https:// URL.
//   * SARATHI_JWT_AUTHORITY_KID, if set, must match the RFC 7638
//     thumbprint of the loaded public key.
//   * If introspection is configured (key present), the key MUST be ≥ 32
//     chars to avoid trivial brute-force.
//   * SARATHI_TLS_CERT_PATH / SARATHI_TLS_KEY_PATH must both be set —
//     publishing JWKS over plain HTTP is forbidden in production.
func EnforceJWTAuthorityProductionGates(a *JWTAuthority) error {
	if a == nil {
		return nil
	}
	if !strings.EqualFold(os.Getenv("SARATHI_ENV"), "production") {
		return nil
	}
	if a.IsEphemeral() {
		return fmt.Errorf("FATAL: ERR_JWT_AUTHORITY_KEY_MISSING — set SARATHI_JWT_AUTHORITY_PRIV_PATH in production")
	}
	iss := strings.TrimSpace(a.Issuer())
	if iss == "" || !strings.HasPrefix(strings.ToLower(iss), "https://") {
		return fmt.Errorf("FATAL: ERR_JWT_AUTHORITY_ISSUER_INSECURE — SARATHI_TOKEN_ISSUER must be a non-empty https:// URL in production (got %q)", iss)
	}
	if want := strings.TrimSpace(os.Getenv(EnvJWTAuthorityKid)); want != "" && want != a.CurrentKid() {
		return fmt.Errorf("FATAL: ERR_JWT_AUTHORITY_KID_MISMATCH — env %q != computed thumbprint %q", want, a.CurrentKid())
	}
	if a.IntrospectionEnabled() && len(a.IntrospectionAPIKey()) < 32 {
		return fmt.Errorf("FATAL: ERR_JWT_INTROSPECTION_KEY_WEAK — SARATHI_JWT_INTROSPECTION_API_KEY must be ≥32 chars in production")
	}
	if os.Getenv("SARATHI_TLS_CERT_PATH") == "" || os.Getenv("SARATHI_TLS_KEY_PATH") == "" {
		return fmt.Errorf("FATAL: ERR_JWT_AUTHORITY_TLS_REQUIRED — JWKS must be served over TLS in production (set SARATHI_TLS_CERT_PATH + SARATHI_TLS_KEY_PATH)")
	}
	return nil
}

// RunServiceRuntime bootstraps the full enforcement pipeline and serves the
// HTTP endpoints until SIGINT/SIGTERM is received. Returns the exit code.
func RunServiceRuntime() int {
	fmt.Println("+-------------------------------------------------------+")
	fmt.Println("|  SARATHI SERVICE RUNTIME                              |")
	fmt.Println("|  Long-lived HTTP enforcement endpoint                 |")
	fmt.Println("|  Every request routes through the Gated Bridge        |")
	fmt.Println("+-------------------------------------------------------+")

	// v15.5: pre-create translation/audit directories so they appear under
	// live/ and proof_logs/ before the first enforcement event fires. Without
	// this, live/translation/ does not exist until a Bucket fan-out has run.
	PrecreateTranslationDirs()

	// ---------- 1. Pre-flight security gates ----------
	cfg := LoadSecureConfig()
	if os.Getenv("SARATHI_SERVICE_REQUIRE_TLS") == "1" && !cfg.TLSEnabled {
		fmt.Fprintln(os.Stderr,
			"FATAL: SARATHI_SERVICE_REQUIRE_TLS=1 but SARATHI_TLS_CERT_PATH / SARATHI_TLS_KEY_PATH not set")
		return 2
	}
	if os.Getenv("SARATHI_SERVICE_REQUIRE_NONDEFAULT_KEYS") == "1" {
		if usingDefaults, systems := cfg.IsUsingDefaultKeys(); usingDefaults {
			fmt.Fprintf(os.Stderr,
				"FATAL: refusing to start with default API keys for %v. "+
					"Set SARATHI_CALLER_KEY_<SYSTEM> for each.\n", systems)
			return 2
		}
	}

	// v15.0: production boot gates. Only fire when SARATHI_ENV=production
	// so development / Stage-A / VC-demo runs are unaffected.
	if strings.EqualFold(os.Getenv("SARATHI_ENV"), "production") {
		mode := ParseInboundAuthMode(os.Getenv("SARATHI_INBOUND_AUTH"))
		if mode == InboundAuthOff {
			fmt.Fprintln(os.Stderr,
				"FATAL: "+CodeInboundAuthOffInProduction+
					" — set SARATHI_INBOUND_AUTH=required in production")
			return 78
		}
		if usingDefaults, systems := cfg.IsUsingDefaultKeys(); usingDefaults {
			fmt.Fprintf(os.Stderr,
				"FATAL: default API keys detected for %v in SARATHI_ENV=production. "+
					"Set SARATHI_CALLER_KEY_<SYSTEM> for each.\n", systems)
			return 78
		}
		// Registry must be non-empty in required-mode production. Load the
		// snapshot directly (cheap) so we fail fast before pipeline init.
		if mode == InboundAuthRequired {
			snapPath := os.Getenv("SARATHI_TRUST_SNAPSHOT")
			remoteURL := os.Getenv("SARATHI_TRUST_REMOTE_URL")
			if snapPath == "" && remoteURL == "" {
				fmt.Fprintln(os.Stderr,
					"FATAL: "+CodeTrustRegistryEmpty+
						" — SARATHI_INBOUND_AUTH=required in production needs "+
						"SARATHI_TRUST_SNAPSHOT or SARATHI_TRUST_REMOTE_URL")
				return 78
			}
			if snapPath != "" {
				snap, err := LoadTrustSnapshot(snapPath)
				if err != nil {
					fmt.Fprintf(os.Stderr, "FATAL: trust snapshot load failed: %v\n", err)
					return 78
				}
				if len(snap.Evaluators) == 0 {
					fmt.Fprintln(os.Stderr,
						"FATAL: "+CodeTrustRegistryEmpty+
							" — snapshot "+snapPath+" has zero evaluators")
					return 78
				}
			}
			// v15.1 Network Surface Closure: pre-flight check on the remote
			// trust URL. Production refuses to bind the listener if (a) the
			// URL is plain http:// — JWKS 2026 best practices forbid it,
			// MITM substitution would forge accepted tokens — or (b) the
			// URL is unreachable on a 5 s GET probe. Either failure exits
			// 78 with a deterministic error code, mirroring the behaviour
			// of the other v15.0 production gates above.
			if remoteURL != "" {
				if code, detail := preflightRemoteTrustURL(remoteURL); code != "" {
					fmt.Fprintf(os.Stderr, "FATAL: %s — %s\n", code, detail)
					return 78
				}
			}
		}
	}

	// ---------- 2. Resolve listen address + bootstrap stack ----------
	listenAddr := os.Getenv("SARATHI_SERVICE_ADDR")
	if listenAddr == "" {
		listenAddr = "127.0.0.1:8443"
	}
	if os.Getenv("SARATHI_WEBHOOK_URL") != "" {
		fmt.Printf("  [service] webhook execution ENABLED: %s\n", os.Getenv("SARATHI_WEBHOOK_URL"))
	} else {
		fmt.Println("  [service] execution handler: simulation (export SARATHI_WEBHOOK_URL to override)")
	}

	boundary, _, err := bootstrapServiceBoundary(listenAddr)
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: %v\n", err)
		return 1
	}

	boundary.PrintEndpoints()

	// ---------- 4. Startup ----------
	errCh := make(chan error, 1)
	go func() {
		errCh <- boundary.Start()
	}()

	// Resolve shutdown deadline.
	shutdownSeconds := 30
	if v, err := strconv.Atoi(os.Getenv("SARATHI_SERVICE_SHUTDOWN_TIMEOUT_S")); err == nil && v > 0 {
		shutdownSeconds = v
	}

	// ---------- 5. Signal wait ----------
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	fmt.Printf("\n[service] ready; pid=%d; listening on %s (ctrl-c to stop)\n",
		os.Getpid(), listenAddr)

	select {
	case err := <-errCh:
		// Server exited on its own — typically a bind error.
		if err != nil {
			fmt.Fprintf(os.Stderr, "[service] HTTP server error: %v\n", err)
			return 1
		}
		return 0
	case sig := <-sigCh:
		fmt.Printf("\n[service] received %s, draining connections (timeout=%ds)...\n",
			sig, shutdownSeconds)
	}

	// ---------- 6. Graceful shutdown ----------
	shutdownErr := boundary.GracefulShutdown(time.Duration(shutdownSeconds) * time.Second)
	if shutdownErr != nil {
		fmt.Fprintf(os.Stderr, "[service] graceful shutdown error: %v\n", shutdownErr)
		return 1
	}

	// Drain the listener goroutine — `ListenAndServe` returns
	// http.ErrServerClosed on a clean shutdown, which we treat as success.
	select {
	case <-errCh:
	case <-time.After(2 * time.Second):
	}
	fmt.Println("[service] shutdown complete")
	return 0
}
