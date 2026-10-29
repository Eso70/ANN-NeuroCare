# Used only by the database migration, before changing the active configuration.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$viteEntry = Join-Path $projectRoot 'frontend\node_modules\vite\bin\vite.js'
$backendDirectory = Join-Path $projectRoot 'backend'
$approved = @()
$allListeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop)
foreach ($port in @(8000, 5173)) {
    $listeners = @($allListeners | Where-Object LocalPort -eq $port)
    foreach ($ownerId in @($listeners.OwningProcess | Select-Object -Unique)) {
        $process = Get-CimInstance Win32_Process -Filter "ProcessId = $ownerId" -ErrorAction Stop
        $command = $process.CommandLine
        $ours = $false
        if ($port -eq 8000) {
            $ours = ($process.Name -match '^python(w)?\.exe$' -and
                $command -match '\buvicorn\s+app\.main:app\b' -and
                $command.Contains($backendDirectory) -and $command -notmatch '--reload')
        } else {
            $ours = ($process.Name -eq 'node.exe' -and $command.Contains($viteEntry))
        }
        if (-not $ours) {
            throw "Port $port is occupied by a process whose NeuroCare ownership cannot be proved. No processes were stopped. Stop the project's launcher normally, then retry."
        }
        $approved += [pscustomobject]@{ Id = $ownerId; CreationDate = $process.CreationDate }
    }
}
# All listeners are validated before stopping any process. Recheck identity to avoid PID reuse.
foreach ($entry in $approved) {
    $current = Get-CimInstance Win32_Process -Filter "ProcessId = $($entry.Id)"
    if ($current -and $current.CreationDate -eq $entry.CreationDate) {
        Stop-Process -Id $entry.Id -ErrorAction Stop
    }
}
$deadline = [DateTime]::UtcNow.AddSeconds(10)
do {
    $remaining = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
        Where-Object LocalPort -in @(8000, 5173))
    if ($remaining.Count -eq 0) { return }
    Start-Sleep -Milliseconds 200
} while ([DateTime]::UtcNow -lt $deadline)
throw 'Application ports did not close. Configuration has not been switched.'
