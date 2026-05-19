# Daily Growth Hub

매일 성장하는 나를 위한 개인 관리 허브

🔗 **배포 주소:** https://jinny777.github.io/daily-growth-hub/

---

## 새 PC에서 시작하기 (한 번만)

### 1. 사전 설치
- [Git](https://git-scm.com/download/win) 설치
- [Python](https://python.org) 설치 (설치 시 **Add Python to PATH** 체크)

### 2. 저장소 클론
```powershell
git clone https://github.com/jinny777/daily-growth-hub.git
cd daily-growth-hub
```

### 3. 자동 셋업 실행
`setup.bat` 파일을 **더블클릭** → Python 패키지, Git 설정 자동 완료

### 4. 웹사이트에서 데이터 동기화
1. https://jinny777.github.io/daily-growth-hub/ 접속
2. **⚙️ 동기화** → GitHub 토큰 입력 → 저장
3. 이후 접속 시 자동으로 데이터 불러와짐

---

## 매일 사용법

| 작업 | 방법 |
|------|------|
| 코드 변경 후 업로드 | `push.bat` 더블클릭 |
| 자동 감지 push | PowerShell에서 `.\auto-push.ps1` 실행 |
| 채용공고 수집 | `python web_job_fetch.py` |
| 지원사업 공고 수집 | `python startup_fetch.py` |

---

## 자동화 (GitHub Actions)

| 작업 | 실행 시간 |
|------|----------|
| 지원사업 공고 수집 | 매일 오전 9시 |
| 채용공고 수집 | 매일 오전 10시 |

→ 웹사이트에서 **🔄 최신 공고 불러오기** 클릭으로 즉시 반영

---

## 기능

- 🙏 기도 제목 작성 및 응답 체크
- ✅ TODO 할 일 관리 + 달력 표기
- 💼 채용공고 관리 (50플러스, Remember 자동 수집)
- 📋 지원사업 공고 관리 (K-startup, Bizinfo 자동 수집)
- 📚 독서 기록
- 🤖 AI 스터디 내용 정리
- 🔔 맞춤형 알림 설정 + Google 캘린더 연동
- ☁️ GitHub 자동 동기화 (다른 PC에서 동일 데이터)
- 📱 PWA 지원 (스마트폰 홈화면에 앱으로 설치)

---

## GitHub 토큰 발급

https://github.com/settings/tokens → Generate new token (classic)

필요 권한: **repo** ✅ **workflow** ✅ **gist** ✅
