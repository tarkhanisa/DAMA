# DAMA Development Workflow

DAMA includes an internal autopilot runner for faster local development.

## Main Command

    cd I:\DAMA
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 <command>

## Commands

Check everything:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 check

Show status:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 status

Ship changes:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 ship "Commit message"

Create database backup:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 backup

## Ship Behavior

The ship command:

1. Runs backend smoke tests.
2. Runs frontend foundation check.
3. Shows Git status.
4. Stages all changes.
5. Commits with the given message.
6. Pushes to GitHub.
