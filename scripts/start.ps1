param(
    [string]$PostgresBin = 'C:\Program Files\PostgreSQL\18\bin'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$backendPython = Join-Path $projectRoot 'backend/.venv/Scripts/python.exe'
$viteEntry = Join-Path $projectRoot 'frontend/node_modules/vite/bin/vite.js'
$logDirectory = Join-Path $projectRoot '.dev-logs'
$ownedProcesses = [System.Collections.Generic.List[object]]::new()

function Test-PortInUse {
    param([int]$Port)
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $connection = $client.ConnectAsync('127.0.0.1', $Port)
        return ($connection.Wait(1000) -and $client.Connected)
    } catch { return $false }
    finally { $client.Dispose() }
}

function Test-AppService {
    param([ValidateSet('Backend','Frontend')][string]$Name)
    try {
        if ($Name -eq 'Backend') {
            $info = Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/' -TimeoutSec 2
            $health = Invoke-RestMethod 'http://127.0.0.1:8000/api/health' -TimeoutSec 2
            return ($info.name -eq 'NeuroCare API' -and $health.status -eq 'ok')
        }
        $page = Invoke-WebRequest 'http://127.0.0.1:5173/' -UseBasicParsing -TimeoutSec 2
        return ($page.StatusCode -eq 200 -and $page.Content -match '<title>NeuroCare AI' -and $page.Content -match '/@vite/client')
    } catch { return $false }
}

function Start-AppService {
    param([string]$Name, [string]$Executable, [string[]]$Arguments)
    $serviceDirectory = $projectRoot
    if ($Name -eq 'Frontend') { $serviceDirectory = Join-Path $projectRoot 'frontend' }
    $process = Start-Process -FilePath $Executable -ArgumentList $Arguments `
        -WorkingDirectory $serviceDirectory -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $logDirectory "$Name.log") `
        -RedirectStandardError (Join-Path $logDirectory "$Name-error.log")
    # Register ownership immediately so partial startup failures also clean up.
    $ownedProcesses.Add([pscustomobject]@{ Name = $Name; Process = $process })
    $deadline = [DateTime]::UtcNow.AddSeconds(30)
    do {
        if ($process.HasExited) { throw "$Name exited during startup. See $logDirectory/$Name-error.log" }
        if (Test-AppService $Name) { Write-Host "$Name is ready."; return }
        Start-Sleep -Milliseconds 300
    } while ([DateTime]::UtcNow -lt $deadline)
    throw "$Name did not become ready within 30 seconds. See $logDirectory/$Name-error.log"
}

Push-Location $projectRoot
try {
    foreach ($requiredFile in @($backendPython, $viteEntry, (Join-Path $projectRoot '.env'))) {
        if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
            throw "Missing prerequisite: $requiredFile. Complete the README setup first."
        }
    }
    $nodeExecutable = (Get-Command node.exe -ErrorAction Stop).Source
    $backendRunning = Test-AppService 'Backend'
    $frontendRunning = Test-AppService 'Frontend'
    # Reject unrelated or unhealthy listeners without terminating them or changing ports.
    if (-not $backendRunning -and (Test-PortInUse 8000)) {
        throw 'Port 8000 is occupied but is not responding as a healthy NeuroCare API. Check that process; it was not stopped.'
    }
    if (-not $frontendRunning -and (Test-PortInUse 5173)) {
        throw 'Port 5173 is occupied but is not responding as the NeuroCare Vite frontend. Check that process; it was not stopped.'
    }

    & (Join-Path $PSScriptRoot 'dev.ps1') db-start -PostgresBin $PostgresBin
    if (-not $?) { throw 'PostgreSQL startup failed.' }
    & (Join-Path $PSScriptRoot 'dev.ps1') migrate
    if (-not $?) { throw 'Database migration failed.' }
    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null

    if ($backendRunning) { Write-Host 'Backend is already running; reusing it.' }
    else {
        # No reload child process: reliable on native Windows and managed terminals.
        Start-AppService 'Backend' $backendPython @('-m','uvicorn','app.main:app','--app-dir',('"' + (Join-Path $projectRoot 'backend') + '"'),'--host','127.0.0.1','--port','8000')
    }
    $database = Invoke-RestMethod 'http://127.0.0.1:8000/api/health/db' -TimeoutSec 8
    if ($database.status -ne 'ok' -or $database.database -ne 'connected') {
        throw 'The backend cannot reach PostgreSQL. Check DB_* (or DATABASE_URL) in the root .env.'
    }
    if ($frontendRunning) { Write-Host 'Frontend is already running; reusing it.' }
    else {
        # Launch Vite directly, avoiding an npm/cmd wrapper and extra console windows.
        Start-AppService 'Frontend' $nodeExecutable @(('"' + $viteEntry + '"'),'--host','127.0.0.1','--port','5173','--strictPort')
    }
    Write-Host "`nNeuroCare is ready: http://127.0.0.1:5173"
    Write-Host 'API documentation: http://127.0.0.1:8000/docs'
    if ($ownedProcesses.Count -eq 0) {
        Write-Host 'All services were already running. No additional servers were started.'
        return
    }
    Write-Host "Logs: $logDirectory"
    Write-Host 'Keep this terminal open. Ctrl+C stops only the API/frontend started here.'
    Write-Host 'PostgreSQL and reused services remain running.'
    while ($true) {
        foreach ($entry in $ownedProcesses) {
            if ($entry.Process.HasExited) {
                throw "$($entry.Name) stopped unexpectedly. See $logDirectory/$($entry.Name)-error.log"
            }
        }
        Start-Sleep -Milliseconds 500
    }
} finally {
    foreach ($entry in $ownedProcesses) {
        if (-not $entry.Process.HasExited) {
            $entry.Process.Kill()
            $entry.Process.WaitForExit(5000) | Out-Null
            Write-Host "Stopped $($entry.Name) started by this launcher."
        }
    }
    Pop-Location
}
