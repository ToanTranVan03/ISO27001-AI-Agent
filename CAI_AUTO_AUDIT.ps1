param(
    [string]$ProjectRoot = "D:\AI_Agent_ISO27001"
)

$ErrorActionPreference = "Stop"
$sourceRoot = $PSScriptRoot
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
$mainFile = Join-Path $ProjectRoot "backend\main.py"
$targetCity = Join-Path $ProjectRoot "frontend-react\src\ISOAgentCity.jsx"

if (-not (Test-Path $mainFile) -or -not (Test-Path $targetCity)) {
    throw "Khong dung thu muc du an: $ProjectRoot. Can co backend\main.py va frontend-react\src\ISOAgentCity.jsx."
}

$relativeFiles = @(
    "backend\auto_audit.py",
    "frontend-react\src\ISOAgentCity.jsx",
    "tests\test_auto_audit_routes.py"
)
foreach ($item in $relativeFiles) {
    if (-not (Test-Path (Join-Path $sourceRoot $item))) {
        throw "Ban va thieu file: $item"
    }
}

$mainText = [System.IO.File]::ReadAllText($mainFile)
if (-not $mainText.Contains("from backend import database, teamwork, enterprise_lab")) {
    throw "Khong tim thay import backend de va. Chua thay doi du an. Gui noi dung main.py de dieu chinh."
}
if (-not $mainText.Contains("    enterprise_lab.init_enterprise_lab()")) {
    throw "Khong tim thay khoi lifespan cua main.py. Chua thay doi du an."
}
if (-not $mainText.Contains("app.include_router(enterprise_router)")) {
    throw "Khong tim thay app.include_router(enterprise_router). Chua thay doi du an."
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupRoot = Join-Path (Split-Path $ProjectRoot -Parent) ("ISO_AgentCity_Backup_" + $stamp)
$backupFiles = @("backend\main.py") + $relativeFiles
foreach ($item in $backupFiles) {
    $source = Join-Path $ProjectRoot $item
    if (Test-Path $source) {
        $destination = Join-Path $backupRoot $item
        New-Item -ItemType Directory -Force -Path (Split-Path $destination -Parent) | Out-Null
        Copy-Item -LiteralPath $source -Destination $destination -Force
    }
}
Write-Host "Da sao luu file cu tai: $backupRoot" -ForegroundColor Cyan

foreach ($item in $relativeFiles) {
    $destination = Join-Path $ProjectRoot $item
    New-Item -ItemType Directory -Force -Path (Split-Path $destination -Parent) | Out-Null
    Copy-Item -LiteralPath (Join-Path $sourceRoot $item) -Destination $destination -Force
    Write-Host "Da cap nhat: $item"
}

# Chi chen 3 dong can thiet; khong ghi de cac route/backend khac.
if (-not $mainText.Contains("enterprise_lab, auto_audit")) {
    $mainText = $mainText.Replace(
        "from backend import database, teamwork, enterprise_lab",
        "from backend import database, teamwork, enterprise_lab, auto_audit")
}
if (-not $mainText.Contains("auto_audit.initialize_auto_audit()")) {
    $mainText = $mainText.Replace(
        "    enterprise_lab.init_enterprise_lab()",
        "    enterprise_lab.init_enterprise_lab()`n    auto_audit.initialize_auto_audit()")
}
if (-not $mainText.Contains("app.include_router(auto_audit.router)")) {
    $mainText = $mainText.Replace(
        "app.include_router(enterprise_router)",
        "app.include_router(enterprise_router)`napp.include_router(auto_audit.router)")
}
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($mainFile, $mainText, $utf8)
Write-Host "Da gan Auto-Audit API vao backend/main.py" -ForegroundColor Green

# Giu cac bai test cu chay trong che do mock khong can PostgreSQL.
foreach ($name in @("test_team_workflow.py", "test_react_auth_routes.py")) {
    $file = Join-Path $ProjectRoot ("tests\" + $name)
    if (Test-Path $file) {
        $text = [System.IO.File]::ReadAllText($file)
        $anchor = "    monkeypatch.setattr(main.enterprise_lab, 'init_enterprise_lab', lambda: None)"
        if ($text.Contains($anchor) -and -not $text.Contains("main.auto_audit, 'initialize_auto_audit'")) {
            $text = $text.Replace($anchor, "$anchor`n    monkeypatch.setattr(main.auto_audit, 'initialize_auto_audit', lambda: None)")
            [System.IO.File]::WriteAllText($file, $text, $utf8)
        }
    }
}
Write-Host "HOAN THANH. Sao luu: $backupRoot" -ForegroundColor Green
Write-Host "Buoc tiep theo: python -m compileall backend; cd frontend-react; npm run build"
