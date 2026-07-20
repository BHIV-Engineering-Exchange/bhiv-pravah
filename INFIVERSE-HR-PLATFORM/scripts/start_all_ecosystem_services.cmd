@echo off
REM Start all BHIV ecosystem services (works from CMD or PowerShell)
REM Usage from repo root:
REM   scripts\start_all_ecosystem_services.cmd
REM   OR:  .\scripts\start_all_ecosystem_services.cmd

cd /d "%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_all_ecosystem_services.ps1" %*
exit /b %ERRORLEVEL%
