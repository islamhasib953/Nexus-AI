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
    $content = Get-Content -LiteralPath $path -Raw
    Assert-Condition ($content.Trim().Length -gt 0) "non-empty: $relativePath"
    return $content
}

foreach ($file in @(
    'apps/api/app/operations/service.py',
    'apps/api/app/api/routes/operations.py',
    'apps/api/migrations/versions/0007_agent_execution_metrics.py',
    'apps/api/tests/test_operations.py',
    'docs/api/phase-14-operations-contract.md',
    'docs/operations/phase-14-observability.md',
    'docs/operations/phase-14-cost-optimization.md',
    'docs/operations/phase-14-incident-runbooks.md',
    'docs/operations/phase-14-backup-recovery.md',
    'docs/operations/phase-14-scaling-roadmap.md',
    'docs/architecture/12-observability-operations.mmd',
    'docs/product/wireframes/04-admin-observability-dashboard.mmd',
    'docs/architecture/ADR-0008-operational-telemetry.md'
)) { [void](Read-Required $file) }

$operations = Read-Required 'apps/api/app/api/routes/operations.py'
Assert-Condition ($operations.Contains('require_operations_access')) 'internal authorization guard exists'
Assert-Condition ($operations.Contains('organization_id')) 'tenant scope is supplied to the service'
$service = Read-Required 'apps/api/app/operations/service.py'
foreach ($metric in @('run_error_rate', 'queue_depth', 'tool_failure_rate', 'cache_hit_rate', 'documents_indexed_chunks')) {
    Assert-Condition ($service.Contains($metric)) "metric is exposed: $metric"
}
$ui = Read-Required 'apps/web/src/App.tsx'
Assert-Condition ($ui.Contains('OperationsDashboard')) 'internal operations dashboard is present'
Assert-Condition ($ui.Contains('getOperationsOverview')) 'dashboard calls the authenticated API'

$diagram = Read-Required 'docs/architecture/12-observability-operations.mmd'
Assert-Condition (($diagram -split "`r?`n")[0].Trim() -eq 'flowchart LR') 'observability diagram is editable Mermaid'
$adr = Read-Required 'docs/architecture/ADR-0008-operational-telemetry.md'
Assert-Condition ($adr -match '(?m)^- Status: accepted$') 'ADR is accepted'
Assert-Condition ($adr -match '(?m)^## Alternatives considered$') 'ADR records alternatives'

Write-Output "PASS: $($passes.Count)"
foreach ($pass in $passes) { Write-Output "  $pass" }
if ($failures.Count -gt 0) {
    Write-Output "FAIL: $($failures.Count)"
    foreach ($failure in $failures) { Write-Output "  $failure" }
    exit 1
}
Write-Output 'Phase 14 repository validation passed.'
