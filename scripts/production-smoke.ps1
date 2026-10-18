param([string]$BaseUrl = "http://localhost:8000")
$ErrorActionPreference = "Stop"
$live = Invoke-RestMethod "$BaseUrl/api/v1/health/live"
if ($live.status -ne "ok") { throw "Liveness check failed" }
$ready = Invoke-RestMethod "$BaseUrl/api/v1/health/ready"
if ($ready.status -ne "ok") { throw "Readiness check failed" }
Write-Output "Production smoke checks passed for $BaseUrl"
