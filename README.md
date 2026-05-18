# Daily Growth Hub

매일 성장하는 나를 위한 개인 관리 허브

🔗 **배포 주소:** https://jinny777.github.io/daily-growth-hub/

---

## 기능

- 🙏 기도 제목 작성 및 응답 체크
- ✅ TODO 할 일 관리 + 달력 표기
- 💼 채용공고 관리 (네이버 메일 자동 수집)
- 📋 지원사업 공고 관리 (D-Day, 구글 캘린더 연동)
- 📚 독서 기록
- 🤖 AI 스터디 내용 정리

---

## 다른 PC에서 작업하기

### 1. 사전 준비 (최초 1회)

**Git 설치**
- https://git-scm.com/download/win 에서 다운로드 후 설치

**Python 설치** (스크립트 실행 시 필요)
- https://python.org 에서 다운로드
- 설치 시 **Add Python to PATH** 반드시 체크

**VS Code 설치** (선택)
- https://code.visualstudio.com

### 2. 저장소 클론

```powershell
git clone https://github.com/jinny777/daily-growth-hub.git
cd daily-growth-hub
```

### 3. 코드 수정 후 배포

```powershell
git add .
git commit -m "변경 내용 설명"
git remote set-url origin https://jinny777:토큰@github.com/jinny777/daily-growth-hub.git
git push origin main
git remote set-url origin https://github.com/jinny777/daily-growth-hub.git
```

> 토큰: https://github.com/settings/tokens 에서 발급 (repo 권한 필요)

---

## Python 스크립트

### 네이버 메일 채용공고 수집
```powershell
python naver_job_fetch.py
```
- 네이버 IMAP 연결 → 채용공고 폴더 → jobs_import.json 생성
- 웹사이트 💼 취업 탭 → 📂 파일 선택 → jobs_import.json

### 지원사업 공고 수집
```powershell
python startup_fetch.py
```
- K-Startup, 기업마당 공고 수집 → programs_import.json 생성
- 웹사이트 📋 지원사업 탭 → 📂 공고 가져오기 → programs_import.json

---

## 데이터 동기화 (다른 PC에서 동일 데이터 사용)

1. 이 PC: 웹사이트 상단 **⚙️ 동기화** → GitHub 토큰 입력 → **☁️ 저장**
2. 다른 PC: 웹사이트 접속 후 **⚙️ 동기화** → 같은 토큰 입력 → **☁️ 불러오기**

또는

1. 이 PC: 상단 **💾** 클릭 → 백업 JSON 다운로드
2. 다른 PC: 상단 **📥** 클릭 → 백업 JSON 선택

---

## 파일 구조

```
daily-growth-hub/
├── index.html          # 메인 웹앱 (모든 기능 포함)
├── sync-data.json      # 클라우드 동기화 데이터 (자동 생성)
├── naver_job_fetch.py  # 네이버 메일 채용공고 수집 스크립트
├── startup_fetch.py    # 지원사업 공고 수집 스크립트
└── README.md           # 이 파일
```
