@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   Daily Growth Hub - 새 PC 셋업
echo ========================================
echo.

:: ── Python 확인 ──
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo https://python.org 에서 설치 후 다시 실행하세요.
    echo 설치 시 "Add Python to PATH" 반드시 체크!
    pause & exit /b
)
echo [OK] Python 확인

:: ── Git 확인 ──
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [오류] Git이 설치되어 있지 않습니다.
    echo https://git-scm.com 에서 설치 후 다시 실행하세요.
    pause & exit /b
)
echo [OK] Git 확인

:: ── Git 사용자 설정 ──
echo.
echo [1/2] Git 사용자 설정...
git config --global user.email "khjyeon777@gmail.com"
git config --global user.name "jinny777"
git config --global credential.helper wincred
echo [OK] Git 설정 완료

:: ── 최신 코드 가져오기 ──
echo.
echo [2/2] 최신 코드 동기화...
git pull --rebase origin main
echo [OK] 최신 코드 가져오기 완료

echo.
echo ========================================
echo   셋업 완료!
echo ========================================
echo.
echo 다음 단계:
echo   1. 웹사이트: https://jinny777.github.io/daily-growth-hub/
echo   2. 상단 [동기화] 버튼으로 데이터 불러오기
echo   3. 코드 수정 후 push.bat 더블클릭으로 배포
echo.
pause
