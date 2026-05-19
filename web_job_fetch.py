"""
채용공고 수집 스크립트
- 서울시 50플러스재단 (JSON API)
- Remember Career (Playwright)
- GroupBy (Playwright - 공개 포지션)
실행: python web_job_fetch.py
"""
import json, re, time, sys
import urllib.request, ssl

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

def fetch_json(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'X-Requested-With': 'XMLHttpRequest',
    })
    try:
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as r:
            return json.loads(r.read().decode('utf-8', errors='replace'))
    except Exception as e:
        print(f"  요청 실패: {e}")
        return None

# ──────────────────────────────────────────
#  서울시 50플러스재단
# ──────────────────────────────────────────
def fetch_50plus():
    print("서울시 50플러스재단 공고 수집 중...")
    results = []
    data = fetch_json('https://www.50plus.or.kr/appListAjax.do?rcrtSeUrl=IN47002&pageIndex=1&pageUnit=30')
    if not data:
        return results
    for item in data.get('list', []):
        ann_no   = item.get('ANN_NO', '')
        title    = item.get('ANN_NM', '').strip()
        org      = item.get('OPER_ORG_NM', '').strip()
        period   = item.get('APPDURNG_STED', '')
        deadline = ''
        if '~' in period:
            d = period.split('~')[-1].strip().replace('.', '-')
            if len(d) == 8 and d.isdigit():
                deadline = f"{d[:4]}-{d[4:6]}-{d[6:]}"
            else:
                deadline = d
        results.append({
            'company':  org,
            'position': title,
            'deadline': deadline,
            'source':   '50플러스',
            'url':      f'https://www.50plus.or.kr/appView.do?ANN_NO={ann_no}',
        })
    print(f"  → {len(results)}건 수집")
    return results

# ──────────────────────────────────────────
#  Remember Career
# ──────────────────────────────────────────
def fetch_remember():
    print("Remember Career 공고 수집 중...")
    results = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://career.rememberapp.co.kr/job/postings', timeout=30000)
            page.wait_for_timeout(4000)

            anchors = page.query_selector_all('a[href*="/job/board/"]')
            seen = set()
            for a in anchors:
                try:
                    href = a.get_attribute('href') or ''
                    if not href or href in seen:
                        continue
                    # 프리미엄 전체보기 링크 제외
                    if 'premium' in href or not re.search(r'/job/board/\d+', href):
                        continue
                    seen.add(href)
                    text = a.inner_text().strip()
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    if len(lines) < 2:
                        continue
                    company  = lines[0]
                    position = lines[1] if len(lines) > 1 else lines[0]
                    url = f'https://career.rememberapp.co.kr{href}' if href.startswith('/') else href
                    results.append({
                        'company':  company,
                        'position': position,
                        'deadline': '',
                        'source':   'Remember',
                        'url':      url,
                    })
                except:
                    pass
            browser.close()
        print(f"  → {len(results)}건 수집")
    except Exception as e:
        print(f"  수집 실패: {e}")
    return results

# ──────────────────────────────────────────
#  GroupBy (로그인 필요 → 회사 공고 페이지 직접 접근)
# ──────────────────────────────────────────
def fetch_groupby():
    print("GroupBy 공고 수집 중...")
    results = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # 스카우트 없이 볼 수 있는 스타트업 리스트 페이지
            page.goto('https://groupby.kr/startups', timeout=30000)
            page.wait_for_timeout(4000)

            # 회사 카드 링크 추출
            anchors = page.query_selector_all('a[href*="/startups/"]')
            startup_links = []
            seen = set()
            for a in anchors:
                href = a.get_attribute('href') or ''
                if href and href not in seen and re.search(r'/startups/[a-z0-9\-]+$', href):
                    seen.add(href)
                    startup_links.append(href)

            print(f"  스타트업 {len(startup_links)}개 발견, 공고 수집 중...")

            # 각 스타트업 채용 페이지 방문
            for link in startup_links[:10]:
                try:
                    company_name = link.rstrip('/').split('/')[-1].replace('-', ' ').title()
                    full_url = f'https://groupby.kr{link}' if link.startswith('/') else link
                    results.append({
                        'company':  company_name,
                        'position': '채용 공고 보기',
                        'deadline': '',
                        'source':   'GroupBy',
                        'url':      full_url,
                    })
                except:
                    pass

            # 포지션 직접 탐색
            page.goto('https://groupby.kr/positions', timeout=30000)
            page.wait_for_timeout(5000)
            pos_anchors = page.query_selector_all('a[href*="/position"], a[href*="/positions/"]')
            for a in pos_anchors:
                try:
                    href = a.get_attribute('href') or ''
                    if not href or href in seen:
                        continue
                    seen.add(href)
                    txt = a.inner_text().strip()
                    lines = [l.strip() for l in txt.split('\n') if l.strip()]
                    if not lines:
                        continue
                    url = f'https://groupby.kr{href}' if href.startswith('/') else href
                    results.append({
                        'company':  lines[1] if len(lines) > 1 else 'GroupBy',
                        'position': lines[0],
                        'deadline': '',
                        'source':   'GroupBy',
                        'url':      url,
                    })
                except:
                    pass

            browser.close()
        if not results:
            # fallback: 사이트 링크만 추가
            results.append({
                'company':  'GroupBy',
                'position': '스타트업 채용공고 (로그인 필요)',
                'deadline': '',
                'source':   'GroupBy',
                'url':      'https://groupby.kr/positions',
            })
        print(f"  → {len(results)}건 수집")
    except Exception as e:
        print(f"  수집 실패: {e}")
        results.append({
            'company':  'GroupBy',
            'position': '채용공고 바로가기',
            'deadline': '',
            'source':   'GroupBy',
            'url':      'https://groupby.kr/positions',
        })
    return results

# ──────────────────────────────────────────
#  메인
# ──────────────────────────────────────────
def main():
    print("=" * 50)
    print("  채용공고 수집")
    print("=" * 50)

    all_jobs = []
    all_jobs.extend(fetch_50plus())
    all_jobs.extend(fetch_remember())
    all_jobs.extend(fetch_groupby())

    ts = int(time.time() * 1000)
    output = []
    for i, job in enumerate(all_jobs):
        output.append({
            'id':          f'web_{ts + i}',
            'createdAt':   ts - i * 1000,
            'company':     job.get('company', ''),
            'position':    job.get('position', ''),
            'deadline':    job.get('deadline', ''),
            'appliedDate': '',
            'status':      '관심',
            'channel':     job.get('source', ''),
            'url':         job.get('url', ''),
            'notes':       f"{job.get('source', '')} 자동 수집",
        })

    with open('jobs_import.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 총 {len(output)}건 → jobs_import.json 저장 완료!")
    print("\n가져오기 방법:")
    print("  웹사이트 💼 취업 탭 → 📂 파일 선택 → jobs_import.json")
    if sys.stdin.isatty():
        input("\n아무 키나 누르면 종료합니다.")

if __name__ == '__main__':
    main()
