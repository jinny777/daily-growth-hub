@echo off
chcp 65001 >nul
echo.
echo ===================================
echo   Daily Growth Hub - 배포 (Push)
echo ===================================
echo.

git pull --rebase origin main

git add .

git diff --staged --quiet
if %errorlevel% == 0 (
    echo 변경사항이 없습니다.
    goto done
)

set /p MSG="커밋 메시지 입력 (빈칸=자동): "
if "%MSG%"=="" set "MSG=Update %date% %time:~0,5%"

git commit -m "%MSG%"
git push origin main

if %errorlevel% == 0 (
    echo.
    echo [완료] GitHub에 배포됐습니다!
    echo https://jinny777.github.io/daily-growth-hub/
) else (
    echo.
    echo [오류] push 실패. 토큰 로그인이 필요할 수 있습니다.
    echo git remote set-url origin https://jinny777:토큰@github.com/jinny777/daily-growth-hub.git
)

:done
echo.
pause
