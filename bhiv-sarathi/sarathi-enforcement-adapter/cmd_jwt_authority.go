package main

// cmd_jwt_authority.go — v15.6 CLI subcommands for the outbound JWT authority.
//
// Operators run these BEFORE booting the service to provision and rotate the
// signing key. They short-circuit before pipeline init (see
// enforcement_adapter_main.go) so a `--bootstrap-jwt-authority` call never
// loads policies / registry / PDP.
//
// Subcommands:
//
//	--bootstrap-jwt-authority [--out=<dir>] [--issuer=<url>] [--audience=<aud>]
//	    [--ttl=<seconds>] [--print-private-key] [--print-introspection-key]
//	    Generates a fresh Ed25519 keypair, persists under <dir> (default
//	    live/keys/jwt_authority/), computes the RFC 7638 kid, optionally prints
//	    the raw private key + introspection API key for out-of-band sharing
//	    with the BHIV Core team.
//
//	--rotate-jwt-authority [--out=<dir>] [--grace-hours=<h>]
//	    Moves the existing current.pub to grace/<old_kid>.pub, writes the
//	    grace_expires sidecar, DELETES current.key (verify-only role for the
//	    grace window), generates a new keypair, and writes current.{key,pub,kid}.
//
//	--inspect-jwt-authority [--out=<dir>]
//	    Loads the authority from disk, prints a human-readable summary (kid,
//	    iss URL when env is set, grace key count + expiries) without booting
//	    the service.
//
// All three append a `JWT_AUTHORITY_*` audit row to proof_logs/registry_audit.jsonl.
//
// TAG: jwt-authority-v15.6

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

// ParseJWTAuthorityCLIArgs is the dispatcher hook from main(). Returns
// (handled, exitCode). When handled=true the binary should os.Exit(code)
// without booting the pipeline.
func ParseJWTAuthorityCLIArgs(args []string) (bool, int) {
	if len(args) < 2 {
		return false, 0
	}
	switch args[1] {
	case "--bootstrap-jwt-authority":
		return true, runBootstrapJWTAuthority(args[2:])
	case "--rotate-jwt-authority":
		return true, runRotateJWTAuthority(args[2:])
	case "--inspect-jwt-authority":
		return true, runInspectJWTAuthority(args[2:])
	}
	return false, 0
}

// resolveJWTAuthorityKeysDir picks the operator-preferred keys directory.
// Order: --out flag, SARATHI_JWT_AUTHORITY_KEYS_DIR env, default.
func resolveJWTAuthorityKeysDir(flags cliFlags) string {
	if v := strings.TrimSpace(flags["out"]); v != "" {
		return v
	}
	if v := strings.TrimSpace(os.Getenv(EnvJWTAuthorityKeysDir)); v != "" {
		return v
	}
	return DefaultJWTAuthorityKeysDir
}

// ============================================================================
// --bootstrap-jwt-authority
// ============================================================================

func runBootstrapJWTAuthority(args []string) int {
	flags, _ := parseCLIFlags(args)
	keysDir := resolveJWTAuthorityKeysDir(flags)
	issuer := strings.TrimSpace(flags["issuer"])
	if issuer == "" {
		issuer = strings.TrimSpace(os.Getenv(EnvTokenIssuer))
	}
	audience := strings.TrimSpace(flags["audience"])
	if audience == "" {
		audience = DefaultJWTAudience
	}
	printPriv := flags["print-private-key"] == "true"
	printIntrospect := flags["print-introspection-key"] == "true"

	// Pre-existing key guard.
	currentKeyPath := filepath.Join(keysDir, "current.key")
	if _, err := os.Stat(currentKeyPath); err == nil {
		fmt.Fprintf(os.Stderr,
			"ERROR: %s already exists. Refusing to overwrite — use --rotate-jwt-authority to rotate.\n",
			currentKeyPath)
		return 2
	}

	signer, err := GenerateLocalEd25519Signer()
	if err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: keygen: %v\n", err)
		return 1
	}
	if err := PersistSignerToDisk(signer, keysDir); err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: persist signer: %v\n", err)
		return 1
	}

	// Mint a fresh introspection API key candidate so the operator can grab
	// it once at bootstrap. Not stored in any snapshot — the operator must
	// export SARATHI_JWT_INTROSPECTION_API_KEY=<value> for the service.
	introspectKey, ierr := generateIntrospectKey()
	if ierr != nil {
		fmt.Fprintf(os.Stderr, "ERROR: introspect key: %v\n", ierr)
		return 1
	}

	// Audit row.
	appendRegistryAudit("JWT_AUTHORITY_BOOTSTRAP", map[string]string{
		"keys_dir":         keysDir,
		"kid":              signer.Kid(),
		"public_key_hex":   hex.EncodeToString(signer.PublicKey())[:32] + "...",
		"issuer_hint":      issuer,
		"audience_hint":    audience,
		"printed_private":  fmt.Sprintf("%t", printPriv),
		"printed_apikey":   fmt.Sprintf("%t", printIntrospect),
	})

	// Operator-facing summary.
	fmt.Printf("Bootstrapped JWT authority under %s\n", keysDir)
	fmt.Printf("  kid:               %s\n", signer.Kid())
	fmt.Printf("  current.key:       %s/current.key  (chmod 0600)\n", keysDir)
	fmt.Printf("  current.pub:       %s/current.pub\n", keysDir)
	fmt.Printf("  current.kid:       %s/current.kid\n", keysDir)
	fmt.Printf("  public_key_hex:    %s\n", hex.EncodeToString(signer.PublicKey()))
	if issuer != "" {
		fmt.Printf("  issuer hint:       %s   (export SARATHI_TOKEN_ISSUER=%q)\n", issuer, issuer)
	} else {
		fmt.Printf("  issuer hint:       <unset>   (export SARATHI_TOKEN_ISSUER=https://...)\n")
	}
	fmt.Printf("  audience hint:     %s   (export SARATHI_TOKEN_AUDIENCE=%q)\n", audience, audience)
	fmt.Println()
	fmt.Println("FOR THE OPERATOR (export before --service):")
	fmt.Printf("  export SARATHI_JWT_AUTHORITY_PRIV_PATH=%s/current.key\n", keysDir)
	fmt.Printf("  export SARATHI_JWT_AUTHORITY_KID=%s\n", signer.Kid())
	if issuer != "" {
		fmt.Printf("  export SARATHI_TOKEN_ISSUER=%q\n", issuer)
	}
	fmt.Printf("  export SARATHI_TOKEN_AUDIENCE=%q\n", audience)
	if printIntrospect {
		fmt.Printf("  export SARATHI_JWT_INTROSPECTION_API_KEY=%s\n", introspectKey)
		fmt.Printf("  introspect fingerprint:  %s\n", sha256HexShort(introspectKey))
	} else {
		fmt.Printf("  # use --print-introspection-key to reveal a freshly-minted API key\n")
	}
	fmt.Println()
	if printPriv {
		fmt.Println("PRIVATE KEY (FORWARD ONLY TO TRUSTED CORE-TEAM CONTACT):")
		fmt.Printf("  private_key (raw): %s\n", hex.EncodeToString(signer.PrivateKey()))
	} else {
		fmt.Println("  (private key not printed — re-run with --print-private-key if you must export it)")
	}
	return 0
}

// ============================================================================
// --rotate-jwt-authority
// ============================================================================

func runRotateJWTAuthority(args []string) int {
	flags, _ := parseCLIFlags(args)
	keysDir := resolveJWTAuthorityKeysDir(flags)
	graceHours := 24
	if v := strings.TrimSpace(flags["grace-hours"]); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 {
			graceHours = n
		}
	}
	currentKeyPath := filepath.Join(keysDir, "current.key")
	if _, err := os.Stat(currentKeyPath); err != nil {
		fmt.Fprintf(os.Stderr,
			"ERROR: %s does not exist. Run --bootstrap-jwt-authority first.\n", currentKeyPath)
		return 2
	}
	currentPubPath := filepath.Join(keysDir, "current.pub")
	pubRaw, err := os.ReadFile(currentPubPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: read current.pub: %v\n", err)
		return 1
	}
	pubBytes, err := decodeHexKey(pubRaw, 32)
	if err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: decode current.pub: %v\n", err)
		return 1
	}
	oldKid, err := ComputeRFC7638Thumbprint(pubBytes)
	if err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: compute old kid: %v\n", err)
		return 1
	}

	graceUntil := time.Now().UTC().Add(time.Duration(graceHours) * time.Hour)
	if err := MoveCurrentToGrace(keysDir, oldKid, graceUntil); err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: move to grace: %v\n", err)
		return 1
	}

	// Generate + persist the new signer.
	signer, err := GenerateLocalEd25519Signer()
	if err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: keygen: %v\n", err)
		return 1
	}
	if err := PersistSignerToDisk(signer, keysDir); err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: persist new signer: %v\n", err)
		return 1
	}

	appendRegistryAudit("JWT_AUTHORITY_ROTATE", map[string]string{
		"keys_dir":         keysDir,
		"old_kid":          oldKid,
		"new_kid":          signer.Kid(),
		"grace_until":      graceUntil.Format(time.RFC3339),
		"grace_hours":      strconv.Itoa(graceHours),
	})

	fmt.Printf("Rotated JWT authority under %s\n", keysDir)
	fmt.Printf("  old kid:        %s   (grace-period; expires %s)\n", oldKid, graceUntil.Format(time.RFC3339))
	fmt.Printf("  new kid:        %s   (current)\n", signer.Kid())
	fmt.Printf("  grace dir:      %s\n", filepath.Join(keysDir, "grace"))
	fmt.Println()
	fmt.Println("BRIDGE-SIDE EFFECT:")
	fmt.Println("  JWKS will publish BOTH kids until grace expires; Bridge will accept tokens")
	fmt.Println("  signed by either kid during the grace window. After grace, only the new kid.")
	return 0
}

// ============================================================================
// --inspect-jwt-authority
// ============================================================================

func runInspectJWTAuthority(args []string) int {
	flags, _ := parseCLIFlags(args)
	keysDir := resolveJWTAuthorityKeysDir(flags)

	// Build a one-shot authority directly from disk (no env overrides for
	// inspect — we report whatever the on-disk state is).
	privPath := filepath.Join(keysDir, "current.key")
	pubPath := filepath.Join(keysDir, "current.pub")
	signer, ephemeral, grace, err := loadOrGenerateSigner(privPath, pubPath, keysDir)
	if err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: load signer: %v\n", err)
		return 1
	}
	if ephemeral {
		fmt.Println("[inspect] WARN: no on-disk key — reporting state of an ephemeral signer")
	}
	auth, err := NewJWTAuthority(JWTAuthorityConfig{
		Signer:    signer,
		GraceKeys: grace,
		Issuer:    os.Getenv(EnvTokenIssuer),
		Audience:  os.Getenv(EnvTokenAudience),
		KeysDir:   keysDir,
		Ephemeral: ephemeral,
	})
	if err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: NewJWTAuthority: %v\n", err)
		return 1
	}

	out, _ := json.MarshalIndent(auth.Summary(), "", "  ")
	fmt.Println(string(out))
	return 0
}

// ============================================================================
// HELPERS
// ============================================================================

// generateIntrospectKey returns a fresh 32-byte hex random suitable for use
// as SARATHI_JWT_INTROSPECTION_API_KEY. Same length convention as
// cmd_sovereign_keygen.go::api_key.
func generateIntrospectKey() (string, error) {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return hex.EncodeToString(b), nil
}

// sha256HexShort returns the first 16 hex chars of sha256(s). Used in operator
// banners to reference an api-key without revealing it.
func sha256HexShort(s string) string {
	h := sha256.Sum256([]byte(s))
	return hex.EncodeToString(h[:])[:16]
}
