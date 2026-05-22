"""
Gmail 원티드 채용공고 수집 + Wanted API로 실제 공고 URL 연동
실행: python gmail_job_fetch.py

Gmail 앱 비밀번호:
  Google 계정 → 보안 → 2단계 인증 → 앱 비밀번호 생성
"""
import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import json
import re
import getpass
import urllib.request
import urllib.parse
import time
from datetime import datetime
import ssl

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993
USERNAME  = "khjyeon777@gmail.com"

WANTED_SENDERS = [
    "recommend-noreply@mail.wantedlab.com",
    "news@newsletter.wantedlab.com",
    "gigs@newsletter.wantedlab.com",
    "noreply@mail.wantedlab.com",
]

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

# ── 텍스트 처리 ──────────────────────────────
def decode_str(s):
    if not s: return ""
    parts = decode_header(s)
    result = ""
    for part, charset in parts:
        if isinstance(part, bytes):
            try: result += part.decode(charset or "utf-8", errors="replace")
            except: result += part.decode("utf-8", errors="replace")
        else: result += str(part)
    return result.strip()

def strip_html(h):
    if not h: return ""
    h = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', h, flags=re.I)
    h = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', h, flags=re.I)
    h = re.sub(r'<[^>]+>', ' ', h)
    for ent, ch in [('&nbsp;',' '),('&amp;','&'),('&lt;','<'),('&gt;','>'),('&quot;','"'),('&#39;',"'")]:
        h = h.replace(ent, ch)
    return re.sub(r'\s{3,}', '\n', h).strip()

def get_body(msg):
    text, html = "", ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain" and not text:
                try:
                    cs = part.get_content_charset() or "utf-8"
                    text = part.get_payload(decode=True).decode(cs, errors="replace")
                except: pass
            elif ct == "text/html" and not html:
                try:
                    cs = part.get_content_charset() or "utf-8"
                    html = part.get_payload(decode=True).decode(cs, errors="replace")
                except: pass
    else:
        try:
            cs = msg.get_content_charset() or "utf-8"
            raw = msg.get_payload(decode=True).decode(cs, errors="replace")
            if msg.get_content_type() == "text/html": html = raw
            else: text = raw
        except: pass
    return html if html else text

# ── Wanted API로 실제 공고 URL 검색 ──────────────
def search_wanted_url(company, position):
    """Wanted 검색 API로 실제 공고 URL 반환"""
    try:
        query = f"{company} {position}"
        encoded = urllib.parse.quote(query)
        api_url = f"https://www.wanted.co.kr/api/chaos/jobs/v2/list?limit=5&offset=0&query={encoded}"
        req = urllib.request.Request(api_url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json',
            'Referer': 'https://www.wanted.co.kr',
        })
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=10) as res:
            data = json.loads(res.read().decode('utf-8'))
            jobs = data.get('data', {}).get('jobs', [])
            for job in jobs:
                j_company = job.get('company', {}).get('name', '')
                j_position = job.get('position', '')
                j_id = job.get('id', '')
                # 회사명 또는 포지션 유사도 체크
                if j_company and company[:4] in j_company:
                    return f"https://www.wanted.co.kr/wd/{j_id}", j_company, j_position
                if j_position and position[:6] in j_position:
                    return f"https://www.wanted.co.kr/wd/{j_id}", j_company, j_position
    except Exception as e:
        pass
    # 검색 페이지 URL로 대체
    q = urllib.parse.quote(f"{company} {position}")
    return f"https://www.wanted.co.kr/search?query={q}", company, position

# ── 이메일에서 공고 파싱 ──────────────────────────
def parse_jobs_from_email(subject, body_text, msg_id):
    jobs = []

    # "이 회사에서 원하고 있어요" - 단일 기업 추천
    if "이 회사에서" in subject or "딱 맞는 채용공고" in subject:
        # 섹션별로 분리 (업종 → 회사명 → 포지션 패턴)
        sections = re.split(r'(?:IT|제조|금융|유통|서비스|교육|바이오|헬스케어|컨텐츠|물류)[,\s]*(?:컨텐츠|서비스)?', body_text)
        seen = set()
        for sect in sections[1:4]:  # 최대 3개 섹션
            lines = [l.strip() for l in sect.split('\n') if l.strip() and len(l.strip()) > 1]
            company, position = "", ""
            for line in lines[:6]:
                if re.search(r'주요업무|자격요건|우대사항|혜택|보러', line): break
                if '📣' in line:
                    position = line.replace('📣','').strip()
                elif not company and 2 < len(line) < 30:
                    company = line
            if company and position and company not in seen:
                seen.add(company)
                url, real_co, real_pos = search_wanted_url(company, position)
                jobs.append({
                    "id": f"wanted_{msg_id}_{len(jobs)}",
                    "createdAt": int(time.time()*1000) - len(jobs)*100,
                    "company": company,
                    "position": position,
                    "deadline": "",
                    "appliedDate": "",
                    "status": "관심",
                    "channel": "원티드",
                    "url": url,
                    "notes": extract_notes(sect),
                })
                print(f"    → {company}: {position[:30]} | {url[:60]}")
                time.sleep(0.5)  # API 속도 제한

    # "포지션 알림" - 여러 공고 목록
    elif "포지션" in subject or "알림" in subject:
        # 회사명 + 포지션 패턴 추출
        # 패턴: 회사명\n포지션명\n지역 • 경력
        pattern = re.compile(
            r'([가-힣A-Za-z0-9\[\]().& ]{2,30})\n'
            r'([가-힣A-Za-z0-9\[\]().,& /-]{5,80})\n'
            r'([서울경기인천부산대구광주대전울산세종제주][가-힣]*)\s*[•·]\s*경력\s*([0-9년~이상-]+)'
        )
        matches = pattern.findall(body_text)

        # 마감일 목록
        deadlines = re.findall(r'마감일\s*:?\s*(\d{2}[./]\d{2}[./]\d{2})', body_text)
        dl_idx = 0

        seen = set()
        for i, (company, position, loc, exp) in enumerate(matches[:8]):
            company = company.strip()
            position = position.strip()
            key = f"{company}_{position}"
            if key in seen: continue
            seen.add(key)
            dl = ""
            if dl_idx < len(deadlines):
                d = re.sub(r'[./]', '-', deadlines[dl_idx])
                parts = d.split('-')
                if len(parts) == 3:
                    dl = f"20{parts[0]}-{parts[1]}-{parts[2]}"
                dl_idx += 1
            url, _, _ = search_wanted_url(company, position)
            jobs.append({
                "id": f"wanted_{msg_id}_{i}",
                "createdAt": int(time.time()*1000) - i*100,
                "company": company,
                "position": position,
                "deadline": dl,
                "appliedDate": "",
                "status": "관심",
                "channel": "원티드",
                "url": url,
                "notes": f"{loc} • 경력 {exp}",
            })
            print(f"    → {company}: {position[:30]} | {url[:60]}")
            time.sleep(0.5)
    return jobs

def extract_notes(text):
    lines = [l.strip() for l in text.split('\n') if l.strip() and not re.search(r'보러|지원|원티드|합격|보상금', l)]
    return '\n'.join(lines[:8])[:400]

# ── 메인 ─────────────────────────────────────────
def main():
    # CI 환경 (GitHub Actions) 에서는 환경변수에서 비밀번호 읽기
    import os, sys
    password = os.environ.get('GMAIL_APP_PASSWORD', '')
    if not password:
        if not sys.stdin.isatty():
            print("[오류] GMAIL_APP_PASSWORD 환경변수가 설정되지 않았습니다.")
            sys.exit(1)
        password = getpass.getpass("Gmail 앱 비밀번호: ")

    print("Gmail 연결 중...")
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(USERNAME, password)
        print("로그인 성공!")
    except Exception as e:
        print(f"로그인 실패: {e}")
        sys.exit(1)

    mail.select("INBOX")

    all_eids = []
    for sender in WANTED_SENDERS:
        try:
            _, ids = mail.search(None, f'FROM "{sender}"')
            if ids[0]: all_eids.extend(ids[0].split())
        except: pass

    # TRASH도 검색
    try:
        mail.select('"[Gmail]/Trash"')
        for sender in WANTED_SENDERS:
            try:
                _, ids = mail.search(None, f'FROM "{sender}"')
                if ids[0]: all_eids.extend(ids[0].split())
            except: pass
        mail.select("INBOX")
    except: pass

    print(f"{len(all_eids)}개 원티드 메일 발견")

    all_jobs = []
    seen_ids = set()

    for eid in reversed(all_eids[-20:]):
        try:
            mail.select("INBOX")
            _, msg_data = mail.fetch(eid, '(RFC822)')
            if not msg_data or not msg_data[0]: continue
            msg = email.message_from_bytes(msg_data[0][1])
            subject  = decode_str(msg['Subject'])
            body     = strip_html(get_body(msg))
            print(f"\n  [{subject[:45]}]")
            jobs = parse_jobs_from_email(subject, body, eid.decode())
            for j in jobs:
                if j['id'] not in seen_ids:
                    all_jobs.append(j)
                    seen_ids.add(j['id'])
        except Exception as e:
            print(f"  오류: {e}")
            continue

    mail.logout()

    out = "wanted_jobs.json"
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)

    print(f"\n총 {len(all_jobs)}개 원티드 채용공고 → {out}")

if __name__ == "__main__":
    main()
