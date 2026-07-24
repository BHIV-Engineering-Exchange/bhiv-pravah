# scripts/preflight_clean.ps1 — v15.1 canonical artefact cleanup (Windows)
#
# Run BEFORE any reviewer-facing demo or any --v14-6 / --live-integration /
# --parallel-execute / --distributed-integration / --failure-demo /
# --service-live-demo run. See scripts/preflight_clean.sh for the full
# rationale; this script is the line-for-line PowerShell equivalent.
#
# WHAT it removes:  live/, proof_logs/, *_results.json, *_report.json,
#                   audit_v14_6_report.{md,json}, sarathi_run_*.log, etc.
#
# WHAT it keeps:    policies/, sarathi_keys.enc, sources, docs.
#
# Usage:
#   .\scripts\preflight_clean.ps1            # clean
#   .\scripts\preflight_clean.ps1 -DryRun    # show what would be removed
#
# TAG: v15.1 network-surface-closure

[CmdletBinding()]
param(
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RootDir   = Split-Path -Parent $ScriptDir
Set-Location $RootDir

function Remove-Target {
    param([string]$Target)
    if (Test-Path $Target) {
        if ($DryRun) {
            Write-Output "[dry-run] Remove-Item -Recurse -Force $Target"
        } else {
            Remove-Item -Recurse -Force $Target
            Write-Output "  removed: $Target"
        }
    }
}

function Remove-Glob {
    param([string]$Pattern)
    Get-ChildItem -Path $RootDir -Filter $Pattern -File -ErrorAction SilentlyContinue |
        ForEach-Object {
            if ($DryRun) {
                Write-Output "[dry-run] Remove-Item -Force $($_.FullName)"
            } else {
                Remove-Item -Force $_.FullName
                Write-Output "  removed: $($_.Name)"
            }
        }
}

Write-Output "== Sarathi v15.1 preflight clean =="
Write-Output "  root: $RootDir"
if ($DryRun) { Write-Output "  mode: DRY-RUN (no files will be removed)" }

# Directories
Remove-Target 'live'
Remove-Target 'proof_logs'
Remove-Target 'multi_node_reports'

# Top-level harness reports
Remove-Glob '*_results.json'
Remove-Glob '*_report.json'
Remove-Glob '*_report_1000.json'
Remove-Glob 'audit_v14_6_report.md'
Remove-Glob 'audit_v14_6_report.json'
Remove-Glob 'propagation_byte_equality_report*.json'
Remove-Glob 'live_integration_report.json'
Remove-Glob 'service_live_integration_report.json'
Remove-Glob 'parallel_execution_report.json'
Remove-Glob 'distributed_integration_report.json'
Remove-Glob 'failure_demo_report.json'
Remove-Glob 'cross_system_integration_report.json'
Remove-Glob 'transport_integrity_report.json'
Remove-Glob 'multi_node_determinism_report.json'
Remove-Glob 'governance_consistency_report.json'
Remove-Glob 'vc_demo_*.json'
Remove-Glob 'vc_demo_*.jsonl'
Remove-Glob 'sarathi_run_*.log'
Remove-Glob 'stderr.log'
Remove-Glob 'stderr_audit.log'
Remove-Glob 'full_output.txt'
Remove-Glob 'out_full.txt'

Write-Output "== preflight clean complete =="
