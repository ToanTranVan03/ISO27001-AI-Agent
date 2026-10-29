param(
    [string]$ProjectRoot = "D:\AI_Agent_ISO27001"
)

$ErrorActionPreference = 'Stop'
$sourceRoot = $PSScriptRoot
$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path

$mainFile = Join-Path $ProjectRoot 'backend\main.py'
if (-not (Test-Path -LiteralPath $mainFile)) { throw "Khong tim thay backend/main.py" }
$mainText = [System.IO.File]::ReadAllText($mainFile)
if (-not $mainText.Contains('app.include_router(auto_audit.router)')) {
    throw "Backend chua tich hop Auto-Audit giai doan truoc. Khong the cap nhat an toan."
}

$relativeFiles = @(
    'backend\auto_audit.py',
    'backend\auto_sources.py',
    'frontend-react\src\ISOAgentCity.jsx',
    'tests\test_auto_sources.py'
)
foreach ($item in $relativeFiles) {
    $origin = Join-Path $sourceRoot $item
    if (-not (Test-Path -LiteralPath $origin)) { throw "Thieu file ban va: $origin" }
}
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backupRoot = Join-Path (Split-Path -Parent $ProjectRoot) ("ISO_AgentCity_GiaiDoan3_Backup_" + $stamp)

foreach ($item in ($relativeFiles + @('backend\team_api.py'))) {
    $old = Join-Path $ProjectRoot $item
    if (Test-Path -LiteralPath $old) {
        $new = Join-Path $backupRoot $item
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $new) | Out-Null
        Copy-Item -LiteralPath $old -Destination $new -Force
    }
}
Write-Host "BACKUP: $backupRoot" -ForegroundColor Cyan

foreach ($item in $relativeFiles) {
    $dest = Join-Path $ProjectRoot $item
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
    $src = (Resolve-Path -LiteralPath (Join-Path $sourceRoot $item)).Path
    $dstFull = [System.IO.Path]::GetFullPath($dest)
    if ($src -ieq $dstFull) {
        Write-Host "File da nam dung cho: $item" -ForegroundColor Yellow
    } else {
        Copy-Item -LiteralPath $src -Destination $dest -Force
        Write-Host "Da cap nhat: $item" -ForegroundColor Cyan
    }
}

# Keep existing team API intact; only annotate future job errors with exception class.
$teamApiPath = Join-Path $ProjectRoot 'backend\team_api.py'
if (Test-Path -LiteralPath $teamApiPath) {
    $text = [System.IO.File]::ReadAllText($teamApiPath)
    $old = "    except Exception:`n        logger.exception('Agent job %s failed',job_id)"
    $new = "    except Exception as exc:`n        logger.exception('Agent job %s failed',job_id)"
    if ($text.Contains($old) -and $text.Contains("'Không thể chạy Agent. Kiểm tra Ollama hoặc log API.'")) {
        $text = $text.Replace($old,$new)
        $text = $text.Replace("'Không thể chạy Agent. Kiểm tra Ollama hoặc log API.'", "f'Agent exception: {type(exc).__name__}. Check FastAPI logs.'")
        $utf8 = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($teamApiPath,$text,$utf8)
        Write-Host 'Da bo sung loai loi cho cac job tu lan chay sau.' -ForegroundColor Green
    } else {
        Write-Host 'Khong va duoc team_api.py (khac phien ban); giu nguyen.' -ForegroundColor Yellow
    }
}
Write-Host 'HOAN THANH. Khong thay doi main.py, App.jsx, .env hoac database cu.' -ForegroundColor Green
Write-Host 'Buoc tiep: python -m compileall backend; npm run build; restart FastAPI.'
