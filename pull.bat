@echo off
chcp 65001 > nul
echo.
echo ========================================
echo   Daily Growth Hub - 최신 코드 가져오기
echo ========================================
echo.

git pull origin main

echo.
echo [v] 완료! 다른 PC에서 작업한 내용이 반영됐습니다.
echo.
pause
