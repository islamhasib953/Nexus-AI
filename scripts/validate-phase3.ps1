$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$failures = [System.Collections.Generic.List[string]]::new()
$passes = [System.Collections.Generic.List[string]]::new()

function Assert-Condition([bool]$condition, [string]$message) {
    if ($condition) { $passes.Add($message) } else { $failures.Add($message) }
}

function Read-Required([string]$relativePath) {
    $path = Join-Path $root $relativePath
    Assert-Condition (Test-Path -LiteralPath $path -PathType Leaf) "exists: $relativePath"
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return '' }
    return Get-Content -LiteralPath $path -Raw
}

$required = @(
    'apps/api/app/core/auth.py',
    'apps/api/app/persistence/database.py',
    'apps/api/app/persistence/models.py',
    'apps/api/app/api/routes/workspace.py',
    'apps/api/tests/test_workspace.py',
    'apps/web/src/App.tsx',
    'apps/web/src/api/client.ts',
    'docs/testing/phase-3-validation-report.md'
)
foreach ($file in $required) { [void](Read-Required $file) }

$workspace = Get-Content -LiteralPath (Join-Path $root 'apps/api/app/api/routes/workspace.py') -Raw
foreach ($route in @('/auth/dev/session', '/me', '/conversations', '/runs/{run_id}/events')) {
    Assert-Condition ($workspace.Contains($route)) "workspace route present: $route"
}
foreach ($event in @('run_started', 'status_changed', 'message_delta', 'run_completed', 'run_cancelled')) {
    Assert-Condition ($workspace.Contains($event)) "SSE lifecycle event present: $event"
}
Assert-Condition ($workspace.Contains('require_owned_conversation')) 'conversation authorization helper is used'
Assert-Condition ($workspace.Contains('require_owned_run')) 'run authorization helper is used'

$auth = Get-Content -LiteralPath (Join-Path $root 'apps/api/app/core/auth.py') -Raw
Assert-Condition ($auth.Contains('hmac.compare_digest')) 'signed token verification is present'
Assert-Condition ($auth.Contains('exp')) 'token expiration is present'

$ui = Get-Content -LiteralPath (Join-Path $root 'apps/web/src/App.tsx') -Raw
foreach ($marker in @('New conversation', 'Sign out', 'Cancel run', 'message_delta', 'workspace')) {
    Assert-Condition ($ui.Contains($marker)) "workspace UI behavior present: $marker"
}

$secretMatches = rg --line-number '(?i)(api[_-]?key|password|secret)\s*[:=]\s*[A-Za-z0-9_\-]{12,}' (Join-Path $root 'apps') (Join-Path $root 'scripts') 2>$null
Assert-Condition ($LASTEXITCODE -eq 1) 'no hard-coded secret-like value in application and script files'
$trailing = rg --line-number '[ \t]+$' (Join-Path $root 'apps') (Join-Path $root 'scripts') 2>$null
Assert-Condition ($LASTEXITCODE -eq 1) 'no trailing whitespace in application and script files'

Write-Output "PASS: $($passes.Count)"
foreach ($pass in $passes) { Write-Output "  $pass" }
if ($failures.Count -gt 0) {
    Write-Output "FAIL: $($failures.Count)"
    foreach ($failure in $failures) { Write-Output "  $failure" }
    exit 1
}
Write-Output 'Phase 3 repository validation passed.'
