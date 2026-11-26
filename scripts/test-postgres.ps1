$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$python = Join-Path $root '.venv/Scripts/python.exe'
$settings = @{}
foreach ($line in (Get-Content -LiteralPath '.env')) {
    if ($line -match '^([A-Z_]+)=(.*)$') { $settings[$Matches[1]] = $Matches[2] }
}
$base = $settings['MIGRATION_DATABASE_URL']
$app = $settings['DATABASE_URL']
$port = $settings['POSTGRES_PORT']
$password = [Uri]::EscapeDataString($settings['EVALUATOR_DB_PASSWORD'])
if (!$base.EndsWith('/compliance_ai') -or !$app.EndsWith('/compliance_ai') -or !$port) {
    throw 'This script expects the local Compose database and port documented in README.'
}
$exists = docker compose exec -T db psql -X -U compliance_migrator -d compliance_ai -Atc "SELECT 1 FROM pg_database WHERE datname = 'compliance_ai_test';"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if ($exists -ne '1') {
    docker compose exec -T db createdb -U compliance_migrator compliance_ai_test
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
$env:TEST_MIGRATION_DATABASE_URL = "$($base)_test"
$env:TEST_DATABASE_URL = "$($app)_test"
$env:TEST_EVALUATOR_DATABASE_URL = "postgresql+psycopg://compliance_evaluator:$password@127.0.0.1:${port}/compliance_ai_test"
$prior = $env:MIGRATION_DATABASE_URL
try {
    $env:MIGRATION_DATABASE_URL = $env:TEST_MIGRATION_DATABASE_URL
    & $python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python -m pytest -q
    exit $LASTEXITCODE
} finally {
    $env:MIGRATION_DATABASE_URL = $prior
}
