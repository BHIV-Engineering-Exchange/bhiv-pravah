package main

// cmd_provider_keygen.go — Provider-aware keypair generator.
//
// Generates a fresh keypair under the active CryptoProvider and writes:
//   - Private key file (mode 0600)         -> <out-dir>/<id>-priv.<ext>
//   - Public key file  (mode 0644)         -> <out-dir>/<id>-pub.<ext>
//
// Extensions:
//   Ed25519                  -> .hex      (matches existing trust-snapshot encoding)
//   Composite-MLDSA65-Ed25519 -> .json    (JSON envelope holding both halves)
//
// Usage:
//
//   sarathi-enforcement-adapter --provider-keygen \
//       --evaluator-id=bhiv.sarathi.enforcement.prod.v1 \
//       --out-dir=./live/keys/sarathi_enforcement \
//       --key-id-rotation=2026-05
//
// The active provider is selected by SARATHI_CRYPTO_PROVIDER (ed25519 by
// default). To generate composite keys, set SARATHI_CRYPTO_PROVIDER=hybrid
// in the environment before invoking this command.
//
// PRIVATE KEY HANDLING:
//   The private key is WRITTEN TO DISK with mode 0600. The command does NOT
//   print private bytes to stdout (defence against terminal logs / CI runner
//   buffers). The on-disk file is the operator's responsibility — Sarathi
//   refuses to load it at boot if mode is not 0600 on POSIX.
//
// TAG: tantra-v15.7

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

func runProviderKeygen(args []string) int {
	flags, _ := parseCLIFlags(args)

	evID := strings.TrimSpace(flags["evaluator-id"])
	if evID == "" {
		fmt.Fprintln(os.Stderr, "provider-keygen: --evaluator-id is required")
		return 2
	}
	if _, err := ParseTantraEvaluatorID(evID); err != nil {
		fmt.Fprintf(os.Stderr, "provider-keygen: %v\n", err)
		return 2
	}

	outDir := strings.TrimSpace(flags["out-dir"])
	if outDir == "" {
		outDir = filepath.Join("live", "keys", safeForFilename(evID))
	}
	if err := os.MkdirAll(outDir, 0o755); err != nil {
		fmt.Fprintf(os.Stderr, "provider-keygen: mkdir %s: %v\n", outDir, err)
		return 1
	}

	rotation := strings.TrimSpace(flags["key-id-rotation"])
	if rotation == "" {
		rotation = time.Now().UTC().Format("2006-01")
	}

	// Ensure provider is initialised.
	provider := InitCryptoProvider()

	priv, pub, err := provider.Generate(nil)
	if err != nil {
		fmt.Fprintf(os.Stderr, "provider-keygen: generate: %v\n", err)
		return 1
	}

	var ext string
	switch provider.Algorithm() {
	case CryptoAlgEd25519:
		ext = ".hex"
	case CryptoAlgCompositeMLDSA65Ed25519:
		ext = ".json"
	default:
		ext = ".key"
	}

	privPath := filepath.Join(outDir, "issuer-priv"+ext)
	pubPath := filepath.Join(outDir, "issuer-pub"+ext)

	privEncoded := provider.EncodePrivateKey(priv)
	pubEncoded := provider.EncodePublicKey(pub)

	if err := os.WriteFile(privPath, []byte(privEncoded), 0o600); err != nil {
		fmt.Fprintf(os.Stderr, "provider-keygen: write priv: %v\n", err)
		return 1
	}
	if err := os.WriteFile(pubPath, []byte(pubEncoded), 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "provider-keygen: write pub: %v\n", err)
		return 1
	}

	// Best-effort chmod on POSIX (no-op on Windows). os.WriteFile sets the
	// mode but some platforms (e.g. Windows ACLs) need an extra Chmod call.
	if runtime.GOOS != "windows" {
		_ = os.Chmod(privPath, 0o600)
	}

	keyID := fmt.Sprintf("%s#%s-%s", evID, algKeyIDSuffix(provider.Algorithm()), rotation)

	fmt.Println("===========================================================")
	fmt.Println("Sarathi Provider Keygen — completed")
	fmt.Println("===========================================================")
	fmt.Printf("provider:       %s\n", provider.Algorithm())
	fmt.Printf("evaluator_id:   %s\n", evID)
	fmt.Printf("key_id:         %s\n", keyID)
	fmt.Printf("private_key:    %s   (mode 0600 — KEEP LOCAL, NEVER FORWARD)\n", privPath)
	fmt.Printf("public_key:     %s   (mode 0644 — SAFE to share with peers)\n", pubPath)
	fmt.Println()
	fmt.Println("To register THIS evaluator's PUBLIC key in the trust snapshot:")
	fmt.Println()
	fmt.Printf("  sarathi-enforcement-adapter --register-tantra-evaluator \\\n")
	fmt.Printf("      --evaluator-id=%s \\\n", evID)
	fmt.Printf("      --schema-version=%s \\\n", TantraSchemaV1)
	fmt.Printf("      --algorithm=%s \\\n", provider.Algorithm())
	fmt.Printf("      --key-id=%s \\\n", keyID)
	fmt.Printf("      --public-key=%q\n", pubEncoded)
	fmt.Println()
	fmt.Println("WHAT TO SHARE WITH OTHER TEAMS:")
	fmt.Printf("  - %s (the public key file)\n", pubPath)
	fmt.Printf("  - key_id: %s\n", keyID)
	fmt.Printf("  - schema_version: %s\n", TantraSchemaV1)
	fmt.Println("  - algorithm:", provider.Algorithm())
	fmt.Println()
	fmt.Println("WHAT TO KEEP IN SARATHI (NEVER FORWARD):")
	fmt.Printf("  - %s (the private key file)\n", privPath)
	fmt.Println()
	fmt.Println("HINT: set these env vars so the runtime can sign:")
	fmt.Printf("  export SARATHI_ENFORCEMENT_PRIV_PATH=%s\n", privPath)
	fmt.Printf("  export SARATHI_ENFORCEMENT_PUB_PATH=%s\n", pubPath)
	fmt.Printf("  export SARATHI_ENFORCEMENT_KEY_ID=%s\n", keyID)
	return 0
}

// algKeyIDSuffix returns the short algorithm tag used in key_id suffixes.
//
//	CryptoAlgEd25519                 -> "ed25519"
//	CryptoAlgCompositeMLDSA65Ed25519 -> "composite-mldsa65-ed25519"
func algKeyIDSuffix(alg CryptoAlgorithmID) string {
	switch alg {
	case CryptoAlgEd25519:
		return "ed25519"
	case CryptoAlgCompositeMLDSA65Ed25519:
		return "composite-mldsa65-ed25519"
	default:
		return "unknown"
	}
}
