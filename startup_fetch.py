"""
지원사업 공고 수집 스크립트
- K-Startup (창업지원포털)
- 기업마당 (BizInfo)
실행: python startup_fetch.py
"""
import urllib.request
import urllib.parse
import json
import re
from datetime import datetime, timedelta
import ssl

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

def fetch(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/html, */*',
    })
    try:
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as res:
            return res.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  ⚠ 요청 실패: {e}")
        return None

def calc_days_left(deadline_str):
    try:
        patterns = ['%Y-%m-%d','%Y.%m.%d','%Y년 %m월 %d일','%Y/%m/%d']
        for pat in patterns:
            try:
                d = datetime.strptime(deadline_str.strip(), pat)
                return (d - datetime.now()).days
            except:
                pass
        # 숫자만 추출해서 시도
        nums = re.findall(r'\d+', deadline_str)
        if len(nums) >= 3:
            d = datetime(int(nums[0]), int(nums[1]), int(nums[2]))
            return (d - datetime.now()).days
    except:
        pass
    return 0

def fetch_kstartup():
    """K-Startup 창업지원포털 공고 수집"""
    print("📡 K-Startup 공고 수집 중...")
    results = []
    url = "https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do?schStr=&pbancSn=&page=1&pageSize=20"
    data = fetch(url)
    if not data:
        return results

    # 각 공고 블록 분리: go_view(N) 기준
    blocks = re.split(r"go_view\((\d+)\)", data)
    # blocks = [before, sn1, block1, sn2, block2, ...]
    for i in range(1, len(blocks)-1, 2):
        sn    = blocks[i]
        block = blocks[i+1]
        # 제목
        t = re.search(r'class="tit">([^<]+)</p>', block)
        # 기관 (두번째 <li> — 첫번째는 제목 반복)
        lis = re.findall(r'<li>([^<]+)</li>', block)
        org = ''
        for li in lis:
            li = li.strip()
            if li and not li.startswith('조회') and not (t and li in t.group(1)):
                org = li
                break
        # 마감일
        d = re.search(r'마감일자\s*(\d{4}-\d{2}-\d{2})', block)
        if not t: continue
        title    = re.sub(r'\s+', ' ', t.group(1)).strip()
        deadline = d.group(1) if d else ''
        results.append({
            'name':     title,
            'org':      org,
            'category': classify_category(title),
            'deadline': deadline,
            'amount':   '',
            'status':   '검토중',
            'source':   'K-startup',
            'url':      f'https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do?pbancSn={sn}',
            'notes':    'K-Startup 공고',
        })
        if len(results) >= 15:
            break

    print(f"  → {len(results)}개 수집")
    return results

def fetch_bizinfo():
    """기업마당 공고 수집"""
    print("📡 기업마당(BizInfo) 공고 수집 중...")
    results = []
    url = "https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/list.do?rows=20&page=1"
    data = fetch(url)
    if not data:
        return results

    # 각 행(tr) 파싱
    rows = re.split(r'<tr[\s>]', data)
    for row in rows:
        # 제목 링크
        m_url   = re.search(r'href=\s*"(/sii/siia/selectSIIA200Detail\.do\?[^"]+pblancId=([^"&\s]+)[^"]*)"', row)
        m_title = re.search(r'title="([^"]+)\s*페이지 이동"', row)
        if not m_url or not m_title: continue

        title = m_title.group(1).strip()
        link  = 'https://www.bizinfo.go.kr' + m_url.group(1)

        # 날짜 범위에서 마감일
        m_date = re.search(r'(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})', row)
        deadline = m_date.group(2) if m_date else ''

        # 기관명 (마감일 뒤 두번째 <td>)
        tds = re.findall(r'<td[^>]*>([^<]+)</td>', row)
        org = ''
        for td in tds:
            td = td.strip()
            if td and not re.match(r'\d{4}-\d{2}-\d{2}', td) and td not in ['경영','기술','시설','인력','수출','기타'] and len(td) > 1:
                org = td
                break

        if not title: continue
        results.append({
            'name':     title,
            'org':      org,
            'category': classify_category(title),
            'deadline': deadline,
            'amount':   '',
            'status':   '검토중',
            'source':   'Bizinfo',
            'url':      link,
            'notes':    '기업마당 공고',
        })
        if len(results) >= 15:
            break

    print(f"  → {len(results)}개 수집")
    return results

def classify_category(title):
    title_lower = title.lower()
    if any(k in title for k in ['R&D','연구','기술개발','개발과제']):        return 'R&D'
    if any(k in title for k in ['글로벌','수출','해외','국제']):             return '글로벌'
    if any(k in title for k in ['교육','훈련','캠프','아카데미','스쿨']):   return '창업교육'
    if any(k in title for k in ['사업화','자금','융자','투자','지원금','보조']): return '사업화자금'
    return '기타'

def parse_date(s):
    if not s: return ''
    s = s.strip()
    nums = re.findall(r'\d+', s)
    if len(nums) >= 3:
        try:
            return f"{nums[0]}-{nums[1].zfill(2)}-{nums[2].zfill(2)}"
        except: pass
    return ''

def add_seed_data():
    """스크래핑 실패 시 대표 공고 시드 데이터"""
    today = datetime.now()
    return [
        {
            'name': '2026년 초기창업패키지',
            'org': '창업진흥원',
            'category': '사업화자금',
            'deadline': (today + timedelta(days=14)).strftime('%Y-%m-%d'),
            'amount': '최대 1억원',
            'status': '검토중',
            'source': 'K-startup',
            'url': 'https://www.k-startup.go.kr',
            'notes': '예비창업자 ~ 창업 3년 이내 대상. 사업화 자금 및 멘토링 지원',
        },
        {
            'name': '2026년 창업도약패키지',
            'org': '창업진흥원',
            'category': '사업화자금',
            'deadline': (today + timedelta(days=21)).strftime('%Y-%m-%d'),
            'amount': '최대 3억원',
            'status': '검토중',
            'source': 'K-startup',
            'url': 'https://www.k-startup.go.kr',
            'notes': '창업 3~7년 이내 도약기 스타트업 대상',
        },
        {
            'name': '글로벌 액셀러레이팅 프로그램',
            'org': '코트라(KOTRA)',
            'category': '글로벌',
            'deadline': (today + timedelta(days=30)).strftime('%Y-%m-%d'),
            'amount': '해외진출 지원',
            'status': '검토중',
            'source': 'K-startup',
            'url': 'https://www.kotra.or.kr',
            'notes': '해외 시장 진출을 위한 현지화 및 네트워킹 지원',
        },
        {
            'name': '스마트공장 보급·확산 사업',
            'org': '중소벤처기업부',
            'category': 'R&D',
            'deadline': (today + timedelta(days=45)).strftime('%Y-%m-%d'),
            'amount': '최대 5,000만원',
            'status': '검토중',
            'source': 'Bizinfo',
            'url': 'https://www.bizinfo.go.kr',
            'notes': '제조 중소기업 스마트공장 구축 지원',
        },
        {
            'name': '창업기업 R&D 사업화 연계 지원',
            'org': '중소기업기술정보진흥원',
            'category': 'R&D',
            'deadline': (today + timedelta(days=10)).strftime('%Y-%m-%d'),
            'amount': '최대 2억원',
            'status': '검토중',
            'source': 'Bizinfo',
            'url': 'https://www.bizinfo.go.kr',
            'notes': '기술창업기업 R&D 자금 및 사업화 연계',
        },
        {
            'name': '예비창업패키지',
            'org': '창업진흥원',
            'category': '사업화자금',
            'deadline': (today + timedelta(days=7)).strftime('%Y-%m-%d'),
            'amount': '최대 4,000만원',
            'status': '검토중',
            'source': 'K-startup',
            'url': 'https://www.k-startup.go.kr',
            'notes': '예비창업자 대상 사업화 지원 및 멘토링',
        },
        {
            'name': '창업교육 전문기관 육성사업',
            'org': '창업진흥원',
            'category': '창업교육',
            'deadline': (today + timedelta(days=60)).strftime('%Y-%m-%d'),
            'amount': '기관별 상이',
            'status': '검토중',
            'source': 'K-startup',
            'url': 'https://www.k-startup.go.kr',
            'notes': '창업 교육 프로그램 운영 기관 지원',
        },
        {
            'name': '해외 민간투자 유치 지원사업',
            'org': '한국벤처투자',
            'category': '글로벌',
            'deadline': (today + timedelta(days=25)).strftime('%Y-%m-%d'),
            'amount': '매칭 투자',
            'status': '검토중',
            'source': 'Bizinfo',
            'url': 'https://www.kvic.or.kr',
            'notes': '해외 VC 및 엑셀러레이터 연계 투자 유치 지원',
        },
    ]

def main():
    print("=" * 50)
    print("  지원사업 공고 수집")
    print("=" * 50)

    all_results = []

    # 실제 스크래핑 시도
    kstartup = fetch_kstartup()
    bizinfo  = fetch_bizinfo()
    all_results.extend(kstartup)
    all_results.extend(bizinfo)

    # 스크래핑 결과가 없으면 시드 데이터 사용
    if len(all_results) < 3:
        print("\n⚠ 스크래핑 결과가 부족합니다. 기본 공고 데이터를 사용합니다.")
        all_results = add_seed_data()

    # Daily Growth Hub 형식으로 변환
    import time
    output = []
    for i, p in enumerate(all_results):
        output.append({
            'id':        f'fetched_{int(time.time()*1000)+i}',
            'createdAt': int(time.time()*1000) - i*1000,
            'name':      p.get('name',''),
            'org':       p.get('org',''),
            'category':  p.get('category','기타'),
            'deadline':  p.get('deadline',''),
            'amount':    p.get('amount',''),
            'status':    p.get('status','검토중'),
            'source':    p.get('source',''),
            'url':       p.get('url',''),
            'notes':     p.get('notes',''),
        })

    out_path = 'programs_import.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 총 {len(output)}개 공고 → {out_path} 저장 완료!")
    print("\n📋 가져오기 방법:")
    print("  1. https://jinny777.github.io/daily-growth-hub/ 접속")
    print("  2. 📋 지원사업 탭 클릭")
    print("  3. '📂 공고 가져오기' 버튼 클릭 → programs_import.json 선택")
    import sys
    if sys.stdin.isatty():
        input("\n아무 키나 누르면 종료합니다.")

if __name__ == '__main__':
    main()
