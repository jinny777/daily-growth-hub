@echo off
chcp 65001 >nul

set "REPO=c:\Users\khjye\OneDrive\바탕 화면\AI Project\daily-growth-hub\daily-growth-hub"
cd /d "%REPO%"

echo.
echo ===================================
echo   Daily Growth Hub - 자동 Push
echo ===================================
echo.

git add .

git diff --staged --quiet
if %errorlevel% == 0 (
    echo 변경사항이 없습니다.
    goto done
)

set "msg=Update %date% %time:~0,5%"
git commit -m "%msg%"

echo.
echo GitHub에 업로드 중...
git push origin main

if %errorlevel% == 0 (
    echo.
    echo 완료! GitHub에 업로드됐습니다.
) else (
    echo.
    echo 오류가 발생했습니다.
)

:done
echo.
pause
