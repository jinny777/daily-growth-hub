# Daily Growth Hub — 프로젝트 컨텍스트

Claude Code가 이 파일을 읽으면 지금까지의 작업 내용을 파악하고 이어서 작업할 수 있습니다.

---

## 프로젝트 개요

- **이름**: Daily Growth Hub
- **배포 URL**: https://jinny777.github.io/daily-growth-hub/
- **GitHub**: https://github.com/jinny777/daily-growth-hub
- **GitHub 사용자**: jinny777
- **이메일**: khjyeon777@gmail.com
- **형태**: 단일 HTML 파일 정적 웹앱 (GitHub Pages 호스팅)
- **스타일**: Tailwind CSS (CDN), Pretendard 폰트

---

## 파일 구조

```
daily-growth-hub/
├── index.html              # 메인 웹앱 (전체 기능 포함, 약 2700줄)
├── manifest.json           # PWA 매니페스트
├── sw.js                   # 서비스 워커 (PWA 오프라인)
├── icon-192.png            # PWA 아이콘
├── icon-512.png            # PWA 아이콘
├── startup_fetch.py        # 지원사업 공고 수집 (K-startup, Bizinfo)
├── web_job_fetch.py        # 채용공고 수집 (50플러스, Remember Career)
├── naver_job_fetch.py      # 네이버 메일 채용공고 수집
├── programs_import.json    # 지원사업 수집 결과 (GitHub Actions 자동 업데이트)
├── jobs_import.json        # 채용공고 수집 결과 (GitHub Actions 자동 업데이트)
├── push.bat                # 원클릭 git pull+commit+push 스크립트
├── auto-push.ps1           # 파일 변경 감지 자동 push (PowerShell)
├── setup.bat               # 새 PC 환경 셋업 자동화
├── make_icons.py           # PWA 아이콘 생성 스크립트
├── find_apis.py            # (임시) API 탐색용 스크립트
├── sync-data.json          # 클라우드 동기화 데이터
├── README.md               # 프로젝트 문서
└── .github/
    └── workflows/
        ├── fetch-programs.yml  # 지원사업 자동 수집 (매일 오전 9시)
        └── fetch-jobs.yml      # 채용공고 자동 수집 (매일 오전 10시)
```

---

## 구현된 주요 기능

### 1. 탭 구성
- 🙏 기도 — 기도 제목 작성, 응답 체크
- ✅ TODO — 할 일 관리, 달력 표기
- 💼 취업 — 채용공고 관리 (자동 수집 연동)
- 📋 지원사업 — 지원사업 공고 관리 (자동 수집 연동)
- 📚 독서 — 독서 기록
- 🤖 AI스터디 — AI 공부 내용 정리
- ⚙️ 관리자 — 관리자 기능

### 2. 지원사업 탭 (최근 개편)
- **사이트별 필터 탭**: K-startup, Bizinfo, 중소벤처24, Startup Plus, 소상공인, 소상공인24
- **카테고리 필터**: 사업화자금, R&D, 글로벌, 창업교육, 기타
- **카드형 UI**: 기관 아이콘, 날짜, 카테고리 뱃지, 신규 뱃지, D-Day(초록), 자세히/캘린더 버튼
- **🔄 최신 공고 불러오기**: GitHub raw URL에서 자동 fetch
- **🔔 알림설정**: 기업 프로필, 카테고리, 알림 방식 설정 패널
- **data field `source`**: 어느 사이트에서 수집했는지 구분

### 3. 채용공고 탭
- **🔄 최신 채용공고 불러오기**: GitHub raw URL에서 자동 fetch
- **📂 파일로 가져오기**: JSON 파일 직접 업로드
- `autoFetchJobs()` 함수로 jobs_import.json 자동 로드

### 4. 자동 동기화 (클라우드)
- **silentCloudSave()**: 데이터 변경 15초 후 GitHub repo에 자동 저장
- **silentCloudLoad()**: 페이지 로드 시 GitHub에서 최신 데이터 자동 로드
- 저장 위치: `jinny777/daily-growth-hub` 레포의 `sync-data.json`
- 타임스탬프 비교로 더 최신 데이터만 로드
- `localStorage.dgh_last_sync` 로 마지막 동기화 시간 추적

### 5. PWA
- manifest.json, sw.js, 아이콘 완비
- 스마트폰 홈화면에 앱으로 설치 가능
- Android: Chrome 메뉴 → 홈 화면에 추가
- iPhone: Safari 공유 버튼 → 홈 화면에 추가

### 6. GitHub Actions 자동화
- `fetch-programs.yml`: 매일 UTC 00:00 (KST 09:00) 실행
- `fetch-jobs.yml`: 매일 UTC 01:00 (KST 10:00) 실행, Playwright 사용
- 수집 후 자동 커밋 & 푸시

### 7. 알림설정 패널 (`openNotiSettings()`)
- 이메일, 기업 프로필 (업종/규모/투자단계/업력/지역)
- 관심 카테고리 다중 선택
- 알림 채널: 이메일, 카카오톡, 앱 푸시(브라우저 권한), 캘린더 동기화
- 알림 주기: 매일/주간/마감일 하루 전
- 캘린더 동기화 ON + 공고 가져올 때 → ICS 파일 자동 다운로드

---

## 핵심 JS 함수 (index.html)

```
state                   전역 상태 객체 (localStorage 저장)
saveState()             로컬 저장 + 15초 후 클라우드 자동 저장 트리거
silentCloudSave()       GitHub API로 sync-data.json 저장 (백그라운드)
silentCloudLoad()       GitHub API에서 최신 데이터 로드 (시작 시)
autoFetchPrograms()     programs_import.json raw URL에서 fetch
autoFetchJobs()         jobs_import.json raw URL에서 fetch
renderPrograms()        지원사업 카드 렌더링 (사이트/카테고리 필터 포함)
filterProgSite(site)    사이트별 필터
filterProgCat(cat)      카테고리별 필터
openNotiSettings()      알림설정 패널 열기
saveNotiSettings()      알림설정 저장
downloadICS(programs)   ICS 파일 생성 및 다운로드
importPrograms(event)   JSON 파일 가져오기 (캘린더 동기화 연동)
importJobsFromFile(e)   채용공고 JSON 파일 가져오기
cloudSave()             수동 클라우드 저장
cloudLoad()             수동 클라우드 불러오기
```

---

## state 객체 구조

```javascript
{
  user: { email, name },
  startDate, dayOffset,
  prayers: [], prayerFilter,
  todos: [], todoFilter, todoCalYear, todoCalMonth,
  jobs: [], jobFilter, jobChannelFilter,
  programs: [], programFilter, programCatFilter, programSiteFilter,
  books: [],
  aiStudy: [], aiTagFilter,
  notiSettings: {
    email, bizType, bizSize, investStage, bizAge, region,
    categories: [],
    channels: { email, kakao, push, calendar },
    frequency: 'weekly'
  }
}
```

---

## 스크래핑 스크립트

### startup_fetch.py
- **K-startup**: `https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do` HTML 파싱
  - `go_view(N)` 패턴으로 공고 ID 추출
  - `class="tit"` 에서 제목, `마감일자 YYYY-MM-DD` 패턴으로 마감일
- **Bizinfo**: `https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/list.do` HTML 파싱
  - `selectSIIA200Detail.do?pblancId=` 패턴으로 링크
  - `title="... 페이지 이동"` 패턴으로 제목
- 스크래핑 실패 시 시드 데이터 사용
- 출력: `programs_import.json` (source 필드 포함)

### web_job_fetch.py
- **50플러스**: `https://www.50plus.or.kr/appListAjax.do?rcrtSeUrl=IN47002&pageIndex=1&pageUnit=30` JSON API
  - `ANN_NM` = 제목, `OPER_ORG_NM` = 기관, `APPDURNG_STED` = 기간
- **Remember Career**: Playwright로 `career.rememberapp.co.kr/job/postings`
  - `a[href*="/job/board/"]` 셀렉터로 링크 추출
  - inner_text에서 회사명/직무명 파싱
- **GroupBy**: 로그인 필요로 링크만 제공
- 출력: `jobs_import.json`

---

## 해결된 주요 이슈

| 이슈 | 해결 방법 |
|------|----------|
| CORS 오류 (sync) | Cache-Control 헤더 제거 |
| GitHub push 인증 | `credential.helper wincred` + workflow 권한 토큰 |
| GitHub Actions push 충돌 | `git pull --rebase` 후 push |
| 한글 인코딩 오류 | `python -X utf8` 또는 `PYTHONIOENCODING=utf-8` |
| input() CI 오류 | `sys.stdin.isatty()` 조건 추가 |
| 사이트 스크래핑 실패 | Playwright 도입 (Remember), JSON API 발견 (50plus) |

---

## 다음 작업 아이디어 (미구현)

- GroupBy 로그인 없이 공고 수집 방법 탐색
- 중소벤처24, Startup Plus, 소상공인24 공고 수집 추가
- 카카오톡 알림 연동 (카카오 API 필요)
- 지원사업 AI 매칭 추천 (notiSettings 기업 프로필 기반)

---

## 새 PC 셋업

1. Git, Python 설치
2. `git clone https://github.com/jinny777/daily-growth-hub.git`
3. `setup.bat` 더블클릭
4. 웹사이트 → ⚙️ 동기화 → 토큰 입력
