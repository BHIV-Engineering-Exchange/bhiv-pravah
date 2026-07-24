// multi_system_router_propagation_test.go — unit tests for RoutePropagation's
// chain-halt semantics. Uses in-process stub handlers (InstallPropagationHandler)
// so the tests exercise only the routing + halt logic, not HTTP delivery.

package main

import (
	"testing"
)

// makeOKHandler returns a RoutingHandler that always succeeds and records the
// RoutedEvent it saw.
func makeOKHandler(dest *[]*RoutedEvent) RoutingHandler {
	return func(event *RoutedEvent) error {
		*dest = append(*dest, event)
		return nil
	}
}

// makeStopHandler returns a RoutingHandler that always returns a
// *PropagationStopError with the given code.
func makeStopHandler(code, hop string) RoutingHandler {
	return func(event *RoutedEvent) error {
		return &PropagationStopError{
			Code:    code,
			Hop:     hop,
			TraceID: "test-trace",
			Detail:  "simulated halt",
		}
	}
}

// TestRoutePropagation_AllInChainDeliver: every in-chain hop succeeds and
// the digest hop also succeeds → AllInChainDelivered == true, ChainHalted == false.
func TestRoutePropagation_AllInChainDeliver(t *testing.T) {
	env, _ := mkEnvForRouter(t)
	router := NewMultiSystemRouter(nil)

	var coreEvents, ifEvents, bucketEvents, intentEvents []*RoutedEvent
	router.InstallPropagationHandler("core_workflow", makeOKHandler(&coreEvents), true, false)
	router.InstallPropagationHandler("insightflow", makeOKHandler(&ifEvents), true, false)
	router.InstallPropagationHandler("bucket", makeOKHandler(&bucketEvents), true, false)
	router.InstallPropagationHandler("intent_layer", makeOKHandler(&intentEvents), false, true)

	res, err := router.RoutePropagation(env)
	if err != nil {
		t.Fatalf("RoutePropagation: %v", err)
	}
	if res.ChainHalted {
		t.Fatalf("chain should not halt when all hops succeed")
	}
	if !res.AllInChainDelivered() {
		t.Fatalf("all in-chain hops should be delivered")
	}
	if len(res.Hops) < 4 {
		t.Fatalf("expected at least 4 hops, got %d", len(res.Hops))
	}
	// Every handler should have seen exactly one call.
	if len(coreEvents) != 1 || len(ifEvents) != 1 || len(bucketEvents) != 1 || len(intentEvents) != 1 {
		t.Fatalf("hop counts drift: core=%d if=%d bucket=%d intent=%d",
			len(coreEvents), len(ifEvents), len(bucketEvents), len(intentEvents))
	}
}

// TestRoutePropagation_ChainHaltsOnFirstBreak: when core_workflow returns a
// *PropagationStopError, insightflow and bucket must NOT be invoked, but
// the digest-only intent_layer MUST still receive its event (isolated).
func TestRoutePropagation_ChainHaltsOnFirstBreak(t *testing.T) {
	env, _ := mkEnvForRouter(t)
	router := NewMultiSystemRouter(nil)

	var coreEvents, ifEvents, bucketEvents, intentEvents []*RoutedEvent
	router.InstallPropagationHandler("core_workflow",
		makeStopHandler(CodeResponseHashMismatch, HopCore), true, false)
	router.InstallPropagationHandler("insightflow", makeOKHandler(&ifEvents), true, false)
	router.InstallPropagationHandler("bucket", makeOKHandler(&bucketEvents), true, false)
	router.InstallPropagationHandler("intent_layer", makeOKHandler(&intentEvents), false, true)
	// Drain: if someone calls core, we'd see it in this list, but we can't
	// capture it through the stop handler. We assert the chain-halt shape.
	_ = coreEvents

	res, err := router.RoutePropagation(env)
	if err != nil {
		t.Fatalf("RoutePropagation: %v", err)
	}
	if !res.ChainHalted {
		t.Fatalf("chain should halt after core_workflow failure")
	}
	if res.HaltHop != "core_workflow" {
		t.Fatalf("halt hop drift: got %s want core_workflow", res.HaltHop)
	}
	if res.HaltCode != CodeResponseHashMismatch {
		t.Fatalf("halt code drift: got %s want %s", res.HaltCode, CodeResponseHashMismatch)
	}
	if res.AllInChainDelivered() {
		t.Fatalf("AllInChainDelivered must be false after chain halt")
	}
	// Remaining in-chain targets must have been skipped — their handlers must
	// NOT have been invoked.
	if len(ifEvents) != 0 {
		t.Fatalf("insightflow should be skipped after chain halt, got %d events", len(ifEvents))
	}
	if len(bucketEvents) != 0 {
		t.Fatalf("bucket should be skipped after chain halt, got %d events", len(bucketEvents))
	}
	// Intent Layer (digest-only, off-chain) MUST still have been invoked.
	if len(intentEvents) != 1 {
		t.Fatalf("intent_layer should still receive its digest event after halt, got %d", len(intentEvents))
	}
	// Every in-chain hop must appear in res.Hops with either delivered=true,
	// chain_halted=true, or the actual failure code.
	sawCoreFailed := false
	sawIfHalted := false
	sawBucketHalted := false
	for _, h := range res.Hops {
		switch h.Target {
		case "core_workflow":
			if h.Delivered {
				t.Fatalf("core_workflow should not be marked delivered")
			}
			if h.ErrorCode == CodeResponseHashMismatch {
				sawCoreFailed = true
			}
		case "insightflow":
			if h.ChainHalted {
				sawIfHalted = true
			}
		case "bucket":
			if h.ChainHalted {
				sawBucketHalted = true
			}
		}
	}
	if !sawCoreFailed {
		t.Fatalf("core hop did not carry CodeResponseHashMismatch")
	}
	if !sawIfHalted {
		t.Fatalf("insightflow hop did not carry chain_halted=true")
	}
	if !sawBucketHalted {
		t.Fatalf("bucket hop did not carry chain_halted=true")
	}
}

// TestRoutePropagation_IntelligenceFailureDoesNotHalt: when intent_layer
// fails (even with a PropagationStopError), the chain must NOT halt because
// the Intelligence Layer is off-chain by contract.
func TestRoutePropagation_IntelligenceFailureDoesNotHalt(t *testing.T) {
	env, _ := mkEnvForRouter(t)
	router := NewMultiSystemRouter(nil)

	var coreEvents, ifEvents, bucketEvents []*RoutedEvent
	router.InstallPropagationHandler("core_workflow", makeOKHandler(&coreEvents), true, false)
	router.InstallPropagationHandler("insightflow", makeOKHandler(&ifEvents), true, false)
	router.InstallPropagationHandler("bucket", makeOKHandler(&bucketEvents), true, false)
	router.InstallPropagationHandler("intent_layer",
		makeStopHandler(CodeResponseHashMismatch, HopIntelligence), false, true)

	res, err := router.RoutePropagation(env)
	if err != nil {
		t.Fatalf("RoutePropagation: %v", err)
	}
	if res.ChainHalted {
		t.Fatalf("intent_layer failure must not halt the chain")
	}
	if !res.AllInChainDelivered() {
		t.Fatalf("in-chain hops should all be delivered")
	}
	// In-chain hops should all have been called.
	if len(coreEvents) != 1 || len(ifEvents) != 1 || len(bucketEvents) != 1 {
		t.Fatalf("in-chain hop counts: core=%d if=%d bucket=%d",
			len(coreEvents), len(ifEvents), len(bucketEvents))
	}
}

// TestRoutePropagation_NilEnvelope: RoutePropagation must return an error
// when given a nil envelope rather than panic.
func TestRoutePropagation_NilEnvelope(t *testing.T) {
	router := NewMultiSystemRouter(nil)
	_, err := router.RoutePropagation(nil)
	if err == nil {
		t.Fatalf("expected error on nil envelope")
	}
}

// TestExtractErrorCodePrefix: spot-check the error code extractor used by
// invokePropagationHop. It must find BULKHEAD_FULL/CIRCUIT_OPEN/etc.
func TestExtractErrorCodePrefix(t *testing.T) {
	cases := []struct{ in, want string }{
		{"BULKHEAD_FULL: target 'x' at 10 concurrent", "BULKHEAD_FULL"},
		{"CIRCUIT_OPEN: target 'y' circuit breaker open", "CIRCUIT_OPEN"},
		{"HTTP_ERROR: target 'z': connection refused", "HTTP_ERROR"},
		{"no prefix here", ""},
		{"", ""},
		{"lowercase: nope", ""},
	}
	for _, c := range cases {
		got := extractErrorCodePrefix(c.in)
		if got != c.want {
			t.Fatalf("in=%q got=%q want=%q", c.in, got, c.want)
		}
	}
}
