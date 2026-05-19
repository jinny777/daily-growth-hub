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

:: ── Python 패키지 설치 ──
echo.
echo [1/3] Python 패키지 설치 중...
pip install playwright --quiet
python -m playwright install chromium
echo [OK] Playwright 설치 완료

:: ── Git 사용자 설정 ──
echo.
echo [2/3] Git 사용자 설정...
git config --global user.email "khjyeon777@gmail.com"
git config --global user.name "jinny777"
git config --global credential.helper wincred
echo [OK] Git 설정 완료

:: ── 저장소 확인 및 Pull ──
echo.
echo [3/3] 최신 코드 동기화...
set "REPO=c:\Users\khjye\OneDrive\바탕 화면\AI Project\daily-growth-hub\daily-growth-hub"

if exist "%REPO%\.git" (
    cd /d "%REPO%"
    git pull --rebase origin main
    echo [OK] 최신 코드 가져오기 완료
) else (
    echo 저장소가 없습니다. 클론 중...
    cd /d "c:\Users\khjye\OneDrive\바탕 화면\AI Project\daily-growth-hub"
    git clone https://github.com/jinny777/daily-growth-hub.git
    echo [OK] 클론 완료
)

echo.
echo ========================================
echo   셋업 완료!
echo ========================================
echo.
echo 다음 단계:
echo   1. push.bat    - 변경사항 GitHub 업로드 (더블클릭)
echo   2. auto-push.ps1 - 자동 감지 후 push (PowerShell)
echo   3. web_job_fetch.py - 채용공고 수집
echo   4. startup_fetch.py - 지원사업 수집
echo.
echo 웹사이트: https://jinny777.github.io/daily-growth-hub/
echo.
pause
