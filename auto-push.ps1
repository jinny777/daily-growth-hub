# Daily Growth Hub - 자동 Push 감시 스크립트
# 실행: PowerShell에서 .\auto-push.ps1

$repoPath = "c:\Users\khjye\OneDrive\바탕 화면\AI Project\daily-growth-hub\daily-growth-hub"
$watchFiles = @("*.html", "*.py", "*.json", "*.yml", "*.md")
$pushDelay = 30  # 변경 감지 후 30초 뒤 push

Set-Location $repoPath
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Daily Growth Hub 자동 Push 시작" -ForegroundColor Cyan
Write-Host "  파일 변경 감지 중... (Ctrl+C로 종료)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $repoPath
$watcher.IncludeSubdirectories = $false
$watcher.EnableRaisingEvents = $true
$watcher.NotifyFilter = [System.IO.NotifyFilters]::LastWrite

$pendingPush = $false
$lastChange = $null

function Push-Changes {
    Set-Location $repoPath
    git add .
    $status = git diff --staged --quiet
    if ($LASTEXITCODE -ne 0) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
        git commit -m "auto: $timestamp"
        git push origin main
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] GitHub 업로드 완료!" -ForegroundColor Green
        } else {
            git pull --rebase origin main
            git push origin main
        }
    }
    $script:pendingPush = $false
}

Register-ObjectEvent $watcher "Changed" -Action {
    $name = $Event.SourceEventArgs.Name
    if ($name -notmatch '\.(html|py|json|yml|md|bat|ps1)$') { return }
    if ($name -match '^\.git|programs_import\.json$') { return }
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 변경 감지: $name" -ForegroundColor Yellow
    $script:pendingPush = $true
    $script:lastChange = Get-Date
} | Out-Null

Write-Host "준비됨. 파일을 수정하면 ${pushDelay}초 후 자동으로 GitHub에 업로드됩니다." -ForegroundColor Gray
Write-Host ""

while ($true) {
    Start-Sleep -Seconds 5
    if ($pendingPush -and $lastChange -and ((Get-Date) - $lastChange).TotalSeconds -ge $pushDelay) {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] GitHub에 업로드 중..." -ForegroundColor Cyan
        Push-Changes
    }
}
