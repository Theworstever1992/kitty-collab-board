# spawn_agents.ps1 — Kitty Collab Board
# Spawns all agents as background PowerShell jobs.
# Run from the kitty-collab-board directory.

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent

Write-Host ""
Write-Host "  /\_____/\" 
Write-Host " /  o   o  \   Kitty Collab Board — Spawning Agents"
Write-Host "( ==  ^  == )  codename: CLOWDER"
Write-Host " )         (   "
Write-Host ""

# ─── Agent definitions ────────────────────────────────────────────────────────
$Agents = @(
    @{ Name = "claude"; Script = "agents\claude_agent.py" },
    @{ Name = "qwen";   Script = "agents\qwen_agent.py" }
)

$Jobs = @()

foreach ($agent in $Agents) {
    $scriptPath = Join-Path $Root $agent.Script
    if (-not (Test-Path $scriptPath)) {
        Write-Host "  [SKIP] $($agent.Name) — script not found: $scriptPath" -ForegroundColor Yellow
        continue
    }

    Write-Host "  [SPAWN] $($agent.Name)..." -NoNewline
    $job = Start-Job -ScriptBlock {
        param($root, $script)
        Set-Location $root
        & python $script
    } -ArgumentList $Root, $scriptPath

    $Jobs += @{ Name = $agent.Name; Job = $job }
    Write-Host " Job ID: $($job.Id)" -ForegroundColor Green
}

Write-Host ""
Write-Host "  All agents spawned. Open Mission Control to monitor:" -ForegroundColor Cyan
Write-Host "    python mission_control.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "  To stop all agents:"
Write-Host "    Get-Job | Stop-Job; Get-Job | Remove-Job"
Write-Host ""

# Keep running and show job status
Write-Host "  Monitoring jobs (Ctrl+C to stop watching)..."
Write-Host ""

try {
    while ($true) {
        Start-Sleep -Seconds 10
        foreach ($entry in $Jobs) {
            $j = Get-Job -Id $entry.Job.Id -ErrorAction SilentlyContinue
            if ($j) {
                $color = if ($j.State -eq "Running") { "Green" } else { "Yellow" }
                Write-Host "  [$($j.State)] $($entry.Name)" -ForegroundColor $color
            }
        }
        Write-Host ""
    }
} catch {
    # Ctrl+C — exit gracefully
    Write-Host "`n  Stopped watching. Jobs are still running in background." -ForegroundColor Cyan
}
