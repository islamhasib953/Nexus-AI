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

$required = @(
    '.env.example', '.gitignore', '.editorconfig', '.pre-commit-config.yaml',
    'docker-compose.yml', '.github/workflows/ci.yml',
    'apps/api/pyproject.toml', 'apps/api/uv.lock', 'apps/api/Dockerfile',
    'apps/api/app/main.py', 'apps/api/tests/test_health.py',
    'apps/web/package.json', 'apps/web/package-lock.json', 'apps/web/tsconfig.json',
    'apps/web/vite.config.ts', 'apps/web/src/App.tsx', 'apps/web/src/api/client.ts',
    'apps/web/src/api/client.test.ts', 'README.md'
)
foreach ($file in $required) { [void](Read-Required $file) }

$envExample = Get-Content -LiteralPath (Join-Path $root '.env.example') -Raw
Assert-Condition ($envExample -match 'MODEL_PROVIDER=mock') 'safe mock provider default is documented'
Assert-Condition ($envExample -match '(?m)^GROQ_API_KEY=$') 'provider key is empty in env example'
Assert-Condition ($envExample -match '(?m)^HUGGINGFACE_API_KEY=$') 'Hugging Face key is empty in env example'

$backend = (Get-ChildItem -LiteralPath (Join-Path $root 'apps/api/app') -Recurse -Filter '*.py' -File | Get-Content -Raw) -join "`n"
foreach ($route in @('/api/v1/health/live', '/api/v1/health/ready', '/api/v1/contract')) {
    Assert-Condition ($backend.Contains($route)) "backend route present: $route"
}
Assert-Condition ($backend.Contains('CorrelationIdMiddleware')) 'correlation middleware is wired'
Assert-Condition ($backend.Contains('ErrorEnvelope')) 'error envelope is wired'

$frontend = Get-Content -LiteralPath (Join-Path $root 'apps/web/src/api/client.ts') -Raw
Assert-Condition (($frontend.Contains('/api/v1/health/live')) -or ($frontend.Contains('/api/v1/auth/dev/session'))) 'frontend calls a versioned backend route'
Assert-Condition ($frontend.Contains('VITE_API_BASE_URL')) 'frontend uses configurable API base URL'

$ci = Get-Content -LiteralPath (Join-Path $root '.github/workflows/ci.yml') -Raw
foreach ($command in @('uv sync --locked', 'uv run pytest', 'npm ci', 'npm run typecheck', 'npm run build')) {
    Assert-Condition ($ci.Contains($command)) "CI command present: $command"
}

$scanFiles = @(
    Get-ChildItem -LiteralPath (Join-Path $root 'apps') -Recurse -File
    Get-ChildItem -LiteralPath (Join-Path $root 'scripts') -Recurse -File
) | Where-Object { $_.Extension -notin @('.pyc', '.db', '.coverage', '.png', '.jpg', '.jpeg', '.gif') }
$scanFiles = $scanFiles | Where-Object {
    $_.FullName -notmatch '[\\/]\.venv[\\/]|[\\/]node_modules[\\/]|[\\/]dist[\\/]|[\\/]__pycache__[\\/]'
}
$secretMatches = $scanFiles | Select-String -Pattern '(?i)(api[_-]?key|password|secret)\s*[:=]\s*[A-Za-z0-9_\-]{12,}' -AllMatches
Assert-Condition (-not $secretMatches) 'no hard-coded secret-like value in application and script files'

$trailingMatches = $scanFiles | Select-String -Pattern '[ \t]+$' -AllMatches
Assert-Condition (-not $trailingMatches) 'no trailing whitespace in application and script files'

Write-Output "PASS: $($passes.Count)"
foreach ($pass in $passes) { Write-Output "  $pass" }
if ($failures.Count -gt 0) {
    Write-Output "FAIL: $($failures.Count)"
    foreach ($failure in $failures) { Write-Output "  $failure" }
    exit 1
}
Write-Output 'Phase 2 repository validation passed.'
