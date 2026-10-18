$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$failures = [System.Collections.Generic.List[string]]::new()
$passes = [System.Collections.Generic.List[string]]::new()

function Assert-Condition([bool]$condition, [string]$message) {
    if ($condition) { $passes.Add($message) } else { $failures.Add($message) }
}

function Read-RequiredFile([string]$relativePath) {
    $path = Join-Path $projectRoot $relativePath
    Assert-Condition (Test-Path -LiteralPath $path -PathType Leaf) "exists: $relativePath"
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return $null }
    $content = Get-Content -LiteralPath $path -Raw
    Assert-Condition ($content.Trim().Length -gt 0) "non-empty: $relativePath"
    return $content
}

$requiredFiles = @(
    'docs/PROJECT_STATUS.md',
    'docs/architecture/phase-1-system-design.md',
    'docs/architecture/phase-1-data-model.md',
    'docs/api/phase-1-api-contract.md',
    'docs/api/openapi-v1.yaml',
    'docs/security/phase-1-security-architecture.md',
    'docs/operations/phase-1-deployment-and-scaling.md',
    'docs/architecture/README.md'
)
foreach ($file in $requiredFiles) { [void](Read-RequiredFile $file) }

$diagramFiles = @(
    '01-system-context.mmd',
    '02-container-component-architecture.mmd',
    '03-request-routing-flow.mmd',
    '04-conversation-run-lifecycle.mmd',
    '05-agent-orchestration-a2a.mmd',
    '06-mcp-tool-execution.mmd',
    '07-rag-ingestion-retrieval-pipeline.mmd',
    '08-approval-action-sequence.mmd',
    '09-deployment-architecture.mmd',
    '10-failure-recovery-fallback-flow.mmd',
    '11-data-model-erd.mmd'
)
$architectureRoot = Join-Path $projectRoot 'docs/architecture'
foreach ($file in $diagramFiles) {
    $relativePath = "docs/architecture/$file"
    $content = Read-RequiredFile $relativePath
    if ($null -eq $content) { continue }
    $firstLine = ($content -split "`r?`n")[0].Trim()
    Assert-Condition ($firstLine -match '^(flowchart|sequenceDiagram|stateDiagram-v2|erDiagram)') "Mermaid type: $file"
    Assert-Condition ($content -notmatch '\\n') "no escaped newline label: $file"
    Assert-Condition ($content -notmatch '<[^>]+>') "no HTML labels: $file"
    Assert-Condition ($content -notmatch '(?m)^\s*end\s*\[') "no reserved end node id: $file"
}

$openApi = Get-Content -LiteralPath (Join-Path $projectRoot 'docs/api/openapi-v1.yaml') -Raw
Assert-Condition ($openApi -match '(?m)^openapi:\s*3\.1\.0\s*$') 'OpenAPI version is 3.1.0'
Assert-Condition ($openApi -match '(?m)^info:\s*$') 'OpenAPI info section exists'
Assert-Condition ($openApi -match '(?m)^paths:\s*$') 'OpenAPI paths section exists'
Assert-Condition ($openApi -match '(?m)^components:\s*$') 'OpenAPI components section exists'
foreach ($path in @('/me:', '/conversations:', '/conversations/{conversationId}/runs:', '/runs/{runId}:', '/runs/{runId}/cancel:', '/runs/{runId}/events:', '/documents:')) {
    Assert-Condition ($openApi.Contains("  $path")) "OpenAPI route exists: $path"
}
foreach ($event in @('run_started', 'status_changed', 'message_delta', 'tool_started', 'tool_completed', 'run_completed', 'run_failed', 'run_cancelled')) {
    Assert-Condition ($openApi.Contains($event) -or (Get-Content (Join-Path $projectRoot 'docs/api/phase-1-api-contract.md') -Raw).Contains($event)) "event contract exists: $event"
}

$adrs = Get-ChildItem -LiteralPath (Join-Path $projectRoot 'docs/decisions') -Filter 'ADR-*.md' -File
Assert-Condition ($adrs.Count -ge 6) "at least six ADRs exist ($($adrs.Count))"
foreach ($adr in $adrs) {
    $adrContent = Get-Content -LiteralPath $adr.FullName -Raw
    Assert-Condition ($adrContent -match '(?m)^- Status: (Accepted|Proposed|Superseded)') "ADR status exists: $($adr.Name)"
    Assert-Condition ($adrContent -match '(?m)^## Decision\s*$') "ADR decision section exists: $($adr.Name)"
    Assert-Condition ($adrContent -match '(?m)^## Alternatives considered\s*$') "ADR alternatives section exists: $($adr.Name)"
}

$status = Get-Content -LiteralPath (Join-Path $projectRoot 'docs/PROJECT_STATUS.md') -Raw
Assert-Condition ($status -match '\| Active phase \| Phase [0-9]+') 'project status identifies an active phase'
Assert-Condition ($status.Contains('| 1 — System Architecture and Technical Design | Complete |')) 'Phase 1 status is complete'

Write-Output "PASS: $($passes.Count)"
foreach ($pass in $passes) { Write-Output "  $pass" }
if ($failures.Count -gt 0) {
    Write-Output "FAIL: $($failures.Count)"
    foreach ($failure in $failures) { Write-Output "  $failure" }
    exit 1
}
Write-Output 'Phase 1 documentation validation passed.'
