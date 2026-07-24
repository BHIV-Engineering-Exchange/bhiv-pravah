package main

// output_tee.go — Stdout Tee for full output preservation.
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Output Preservation (v14.4)
// Host Organization: Blackhole Infiverse (BHIV)
//
// PURPOSE:
//   Captures ALL stdout output to a timestamped log file while still
//   displaying it on the terminal. This solves the Windows terminal
//   scrollback buffer limitation where early output is lost.
//
// DESIGN:
//   Uses os.Pipe() to intercept os.Stdout. A goroutine reads from the
//   pipe and writes to both the original terminal and a log file.
//   The approach is transparent — no changes needed to fmt.Printf calls.

import (
	"fmt"
	"io"
	"os"
	"sync"
	"time"
)

// outputTeeState holds the tee writer state for cleanup.
type outputTeeState struct {
	logFile    *os.File
	origStdout *os.File
	pipeW      *os.File
	done       chan struct{}
}

// setupOutputTee intercepts os.Stdout so all fmt.Printf/Println output
// goes to both the terminal and a timestamped log file.
//
// Returns the state for cleanup. Call cleanupOutputTee() when done.
// If SARATHI_OUTPUT_LOG env var is set, uses that path instead of the default.
//
// On any setup failure, returns nil and leaves stdout unchanged.
func setupOutputTee() *outputTeeState {
	// Determine log file path
	logPath := os.Getenv("SARATHI_OUTPUT_LOG")
	if logPath == "" {
		logPath = fmt.Sprintf("sarathi_run_%s.log", time.Now().Format("20060102_150405"))
	}

	logFile, err := os.OpenFile(logPath, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[WARN] Could not open output log %s: %v (continuing without log)\n", logPath, err)
		return nil
	}

	// Save the original stdout
	origStdout := os.Stdout

	// Create a pipe
	pipeR, pipeW, err := os.Pipe()
	if err != nil {
		logFile.Close()
		fmt.Fprintf(os.Stderr, "[WARN] Could not create stdout pipe: %v (continuing without log)\n", err)
		return nil
	}

	// Replace os.Stdout with the write end of the pipe
	os.Stdout = pipeW

	done := make(chan struct{})

	// Goroutine: read from pipe, write to both original stdout and log file
	go func() {
		defer close(done)
		var mu sync.Mutex
		buf := make([]byte, 4096)
		for {
			n, err := pipeR.Read(buf)
			if n > 0 {
				mu.Lock()
				origStdout.Write(buf[:n])
				logFile.Write(buf[:n])
				mu.Unlock()
			}
			if err != nil {
				break
			}
		}
	}()

	// Print where the log is going (to the original stdout so it's visible even if pipe fails)
	fmt.Fprintf(origStdout, "  [OUTPUT] Full output being saved to: %s\n", logPath)

	return &outputTeeState{
		logFile:    logFile,
		origStdout: origStdout,
		pipeW:      pipeW,
		done:       done,
	}
}

// cleanupOutputTee restores os.Stdout and closes the log file.
// Must be called before process exit to ensure all output is flushed.
func cleanupOutputTee(state *outputTeeState) {
	if state == nil {
		return
	}

	// Close the write end of the pipe — this causes the goroutine to exit
	state.pipeW.Close()

	// Wait for the goroutine to finish flushing
	<-state.done

	// Restore original stdout
	os.Stdout = state.origStdout

	// Sync and close log file
	state.logFile.Sync()
	state.logFile.Close()
}

// writeOutputTeeFooter writes the final location message after restoring stdout.
func writeOutputTeeFooter(state *outputTeeState) {
	if state == nil {
		return
	}
	// Write to log file directly before cleanup
	io.WriteString(state.logFile, "\n[END OF OUTPUT LOG]\n")
}
