param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('start','install','backend','frontend','migrate','test','check','db-start','db-run','db-stop','db-create','db-setup')]
    [string]$Task,
    [string]$Python = 'C:\Users\esma3\AppData\Local\Programs\Python\Python311\python.exe',
    [string]$PostgresBin = 'C:\Program Files\PostgreSQL\18\bin'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$backendPython = Join-Path $projectRoot 'backend/.venv/Scripts/python.exe'
function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Executable failed with exit code $LASTEXITCODE" }
}
function Get-DatabaseConfig {
    Push-Location (Join-Path $projectRoot 'backend')
    try {
        $configJson = @'
import json
from sqlalchemy.engine import make_url
from app.core.config import get_settings
try:
    url = make_url(get_settings().database_url)
    print(json.dumps(dict(host=url.host or '127.0.0.1', port=url.port or 5432,
                          user=url.username, database=url.database)))
except Exception:
    raise SystemExit('Invalid database configuration. Check DB_* (or DATABASE_URL) in the root .env.')
'@ | & $backendPython -
        if ($LASTEXITCODE -ne 0) { throw 'Could not read the configured database connection.' }
        return ($configJson | ConvertFrom-Json)
    } finally { Pop-Location }
}
function Assert-ProjectClusterTarget {
    # A configured external server must never cause the preserved cluster to be
    # rebound or stopped. Its previous startup options record its actual port.
    if ($databaseConfig.port -eq 5432) {
        throw 'Port 5432 is reserved for the existing independently managed PostgreSQL service. This helper will never launch or stop a server on that port.'
    }
    if ($databaseConfig.host -notin @('127.0.0.1','localhost','::1')) {
        throw 'The configured database is external. Manage that PostgreSQL server separately.'
    }
    $optionsFile = Join-Path $projectRoot '.postgres-data/postmaster.opts'
    $clusterPort = $null
    if (Test-Path -LiteralPath $optionsFile) {
        $options = Get-Content -LiteralPath $optionsFile -Raw
        if ($options -match '"?-p"?\s+"?(\d+)"?') { $clusterPort = [int]$Matches[1] }
    }
    if ($null -eq $clusterPort) {
        throw 'The project cluster has no recorded explicit port. Refusing to start, rebind, or stop it automatically. Manage the selected PostgreSQL server separately.'
    }
    if ($databaseConfig.port -ne $clusterPort) {
        throw "The preserved project cluster uses port $clusterPort, but DATABASE_URL selects $($databaseConfig.port). Start/manage the selected external PostgreSQL server separately; the project cluster was not changed."
    }
}
function Test-ExistingPostgres {
    & (Join-Path $PostgresBin 'pg_isready.exe') -h $databaseConfig.host -p $databaseConfig.port -t 2 *> $null
    $readinessCode = $LASTEXITCODE
    if ($readinessCode -eq 0) {
        Write-Host "PostgreSQL is already running on $($databaseConfig.host):$($databaseConfig.port). Reusing it; no second server was started."
        return $true
    }
    if ($readinessCode -eq 1) {
        throw "PostgreSQL is already on port $($databaseConfig.port) but is not ready yet. Wait for startup/recovery, then retry. No second server was started."
    }
    if ($readinessCode -ne 2) {
        throw "Could not check PostgreSQL readiness (exit code $readinessCode). No server was started."
    }
    return $false
}
Push-Location $projectRoot
try {
    if ($Task -like 'db-*') { $databaseConfig = Get-DatabaseConfig }
    switch ($Task) {
        'start' { & (Join-Path $PSScriptRoot 'start.ps1') -PostgresBin $PostgresBin }
        'install' {
            if (-not (Test-Path -LiteralPath $backendPython)) {
                Invoke-Checked $Python @('-m','venv','backend/.venv')
            }
            Invoke-Checked $backendPython @('-m','pip','install','-r','backend/requirements.txt')
            $frozen = & $backendPython -m pip freeze
            if ($LASTEXITCODE -ne 0) { throw 'Could not freeze Python dependencies' }
            $frozen | Set-Content backend/requirements.lock.txt
            Invoke-Checked 'npm.cmd' @('install','--prefix','frontend')
        }
        'backend' {
            Set-Location backend
            Invoke-Checked $backendPython @('-m','uvicorn','app.main:app','--reload','--host','127.0.0.1','--port','8000')
        }
        'frontend' { Invoke-Checked 'npm.cmd' @('run','dev','--prefix','frontend') }
        'migrate' { Set-Location backend; Invoke-Checked $backendPython @('-m','alembic','upgrade','head') }
        'db-setup' {
            Invoke-Checked $backendPython @((Join-Path $PSScriptRoot 'migrate-postgres.py'),'--setup-only')
        }
        'test' { Set-Location backend; Invoke-Checked $backendPython @('-m','pytest','-q') }
        'check' {
            Invoke-Checked $backendPython @('-m','ruff','check','backend')
            Invoke-Checked 'npm.cmd' @('run','lint','--prefix','frontend')
            Invoke-Checked 'npm.cmd' @('run','build','--prefix','frontend')
        }
        'db-start' {
            if (Test-ExistingPostgres) { break }
            Assert-ProjectClusterTarget
            $data = Join-Path $projectRoot '.postgres-data'
            if (-not (Test-Path -LiteralPath (Join-Path $data 'PG_VERSION'))) {
                throw 'Initialize the local database first using the README, or use Docker Compose.'
            }
            & (Join-Path $PostgresBin 'pg_ctl.exe') -D $data status
            if ($LASTEXITCODE -eq 0) {
                throw 'The project database process exists but is not accepting connections. Check its log before restarting it.'
            }
            Invoke-Checked (Join-Path $PostgresBin 'pg_ctl.exe') @('-D',$data,'-l',(Join-Path $projectRoot '.postgres.log'),'-o',"-h 127.0.0.1 -p $($databaseConfig.port)",'-w','start')
        }
        'db-run' {
            if (Test-ExistingPostgres) { break }
            Assert-ProjectClusterTarget
            $data = Join-Path $projectRoot '.postgres-data'
            if (-not (Test-Path -LiteralPath (Join-Path $data 'PG_VERSION'))) {
                throw 'Initialize the local cluster first using the README.'
            }
            & (Join-Path $PostgresBin 'pg_ctl.exe') -D $data status
            if ($LASTEXITCODE -eq 0) {
                throw 'The project database process exists but is not accepting connections. Check its log before restarting it.'
            }
            # Keep the server attached to this terminal when background helpers are reaped.
            Invoke-Checked (Join-Path $PostgresBin 'postgres.exe') @('-D',$data,'-h','127.0.0.1','-p',"$($databaseConfig.port)")
        }
        'db-stop' {
            Assert-ProjectClusterTarget
            Invoke-Checked (Join-Path $PostgresBin 'pg_ctl.exe') @('-D',(Join-Path $projectRoot '.postgres-data'),'-m','fast','-w','stop')
        }
        'db-create' {
            Assert-ProjectClusterTarget
            Push-Location (Join-Path $projectRoot 'backend')
            try {
                @'
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url
from app.core.config import get_settings
try:
    url = make_url(get_settings().database_url)
    with psycopg.connect(host=url.host, port=url.port or 5432, user=url.username,
                         password=url.password, dbname='postgres',
                         connect_timeout=5, autocommit=True) as connection:
        connection.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(url.database)))
except Exception:
    raise SystemExit('Database creation failed; check configuration, permissions and whether it already exists. No existing database was deleted.')
'@ | & $backendPython -
                if ($LASTEXITCODE -ne 0) { throw 'Database creation failed.' }
            } finally { Pop-Location }
        }
    }
} finally { Pop-Location }
