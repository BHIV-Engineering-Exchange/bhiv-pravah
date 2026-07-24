package main

import "time"

// Clock provides an injectable time source for deterministic evaluation.
// Production uses RealClock. Replay tests use DeterministicClock.
type Clock interface {
	NowUTC() time.Time
}

// RealClock returns the actual system time. Used in production.
type RealClock struct{}

func (RealClock) NowUTC() time.Time {
	return time.Now().UTC()
}

// DeterministicClock returns a fixed timestamp. Used in replay testing.
type DeterministicClock struct {
	FixedTime time.Time
}

func (c DeterministicClock) NowUTC() time.Time {
	return c.FixedTime
}
