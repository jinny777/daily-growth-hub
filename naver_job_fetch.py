"""
네이버 메일 채용공고 폴더 → Daily Growth Hub 가져오기 스크립트
실행: python naver_job_fetch.py
"""
import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import json
import re
import getpass
from datetime import datetime

IMAP_HOST   = "imap.naver.com"
IMAP_PORT   = 993
USERNAME    = "khjyeon@naver.com"
JOB_FOLDER  = "&zETGqaz1rOA-"   # 채용공고 (IMAP modified UTF-7 인코딩)

def decode_str(s):
    if not s: return ""
    parts = decode_header(s)
    result = ""
    for part, charset in parts:
        if isinstance(part, bytes):
            try:
                result += part.decode(charset or "utf-8", errors="replace")
            except Exception:
                result += part.decode("utf-8", errors="replace")
        else:
            result += str(part)
    return result.strip()

def get_body(msg):
    """HTML 본문 우선 저장 (웹에서 렌더링), 없으면 텍스트"""
    text_body = ""
    html_body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain" and not text_body:
                try:
                    cs = part.get_content_charset() or "utf-8"
                    text_body = part.get_payload(decode=True).decode(cs, errors="replace")
                except Exception:
                    pass
            elif ct == "text/html" and not html_body:
                try:
                    cs = part.get_content_charset() or "utf-8"
                    html_body = part.get_payload(decode=True).decode(cs, errors="replace")
                except Exception:
                    pass
    else:
        try:
            cs = msg.get_content_charset() or "utf-8"
            raw = msg.get_payload(decode=True).decode(cs, errors="replace")
            if msg.get_content_type() == "text/html":
                html_body = raw
            else:
                text_body = raw
        except Exception:
            pass

    # HTML이 있으면 원본 HTML 저장 (웹에서 iframe으로 렌더링됨)
    if html_body.strip():
        return html_body  # HTML 원본 저장 (크기 제한 없음)
    # 텍스트만 있으면 정리 후 저장
    body = re.sub(r'\n{3,}', '\n\n', text_body).strip()
    return body

def strip_html(html):
    """HTML 태그 제거"""
    if not html: return ""
    html = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<[^>]+>', ' ', html)
    html = html.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    html = re.sub(r'\s{3,}', '\n\n', html)
    return html.strip()

JOB_URL_PATTERNS = [
    # 채용 사이트별 공고 URL 패턴
    r'https?://[^\s"\'<>]*saramin\.co\.kr/[^\s"\'<>]*rec[-_]?idx[^\s"\'<>]*',
    r'https?://[^\s"\'<>]*saramin\.co\.kr/[^\s"\'<>]*recruit[^\s"\'<>]*',
    r'https?://[^\s"\'<>]*jobkorea\.co\.kr/[^\s"\'<>]*Recruit[^\s"\'<>]*',
    r'https?://[^\s"\'<>]*wanted\.co\.kr/[^\s"\'<>]*wd/[^\s"\'<>]*',
    r'https?://[^\s"\'<>]*work\.go\.kr/[^\s"\'<>]*',
    r'https?://[^\s"\'<>]*incruit\.com/[^\s"\'<>]*job[^\s"\'<>]*',
    r'https?://[^\s"\'<>]*jobplanet\.co\.kr/[^\s"\'<>]*job[^\s"\'<>]*',
    r'https?://[^\s"\'<>]*catch\.co\.kr/[^\s"\'<>]*job[^\s"\'<>]*',
    r'https?://[^\s"\'<>]*remember\.co/[^\s"\'<>]*job[^\s"\'<>]*',
    r'https?://[^\s"\'<>]*linkedin\.com/[^\s"\'<>]*jobs[^\s"\'<>]*',
]
# 공고 바로가기 버튼 텍스트 패턴
JOB_BTN_TEXTS = ['지원하기', '공고 보기', '공고보기', '바로가기', '채용공고', '상세보기', '지원바로가기', '공고 확인', '지원하러 가기']

def extract_job_url(html_body):
    """이메일 HTML에서 채용공고 URL 추출"""
    if not html_body:
        return ""

    # 1. 채용 사이트 URL 패턴 직접 탐색
    for pattern in JOB_URL_PATTERNS:
        m = re.search(pattern, html_body, re.IGNORECASE)
        if m:
            url = m.group(0).rstrip('.,;)')
            return url

    # 2. 버튼/링크 텍스트 기반 탐색 (href 추출)
    for btn_text in JOB_BTN_TEXTS:
        # <a href="URL">버튼텍스트</a> 패턴
        pattern = r'href=["\']([^"\']+)["\'][^>]*>[^<]*' + re.escape(btn_text)
        m = re.search(pattern, html_body, re.IGNORECASE)
        if m:
            url = m.group(1)
            if url.startswith('http'):
                return url
        # 반대 순서: 텍스트 앞에 href
        pattern2 = re.escape(btn_text) + r'[^<]*</a[^>]*>.*?href=["\']([^"\']+)["\']'
        m2 = re.search(pattern2, html_body, re.IGNORECASE | re.DOTALL)
        if m2:
            url = m2.group(1)
            if url.startswith('http'):
                return url

    # 3. 첫 번째 외부 링크 (http로 시작하는 것 중 트래킹 URL 제외)
    all_links = re.findall(r'href=["\']([^"\']+)["\']', html_body)
    for link in all_links:
        if link.startswith('http') and not any(x in link for x in ['unsubscribe','unsub','track','open?','click?','email','mail']):
            return link

    return ""

CHANNEL_RULES = [
    ('사람인',   ['사람인', 'saramin']),
    ('고용24',   ['고용24', 'worknet', '워크넷', '고용센터', '일자리 정보']),
    ('잡코리아', ['잡코리아', 'jobkorea']),
    ('원티드',   ['원티드', 'wanted']),
    ('링크드인', ['linkedin', '링크드인']),
    ('리멤버',   ['리멤버', 'remember']),
    ('인크루트', ['인크루트', 'incruit']),
    ('잡플래닛', ['잡플래닛', 'jobplanet']),
    ('캐치',     ['캐치', 'catch']),
]
APPLIED_KEYWORDS = ['이력서 열람','지원하신','입사지원','지원완료','지원 확인','지원서 확인','지원이 완료','열람하였','귀하의 이력서','지원서를 검토']

def detect_channel(company, notes):
    text = (company + ' ' + notes).lower()
    for name, kws in CHANNEL_RULES:
        if any(k.lower() in text for k in kws):
            return name
    return '기타'

def auto_status(subject, notes):
    text = subject + ' ' + notes
    if any(k in text for k in APPLIED_KEYWORDS):
        return '지원완료'
    return '관심'

def parse_date(date_str):
    try:
        return parsedate_to_datetime(date_str).strftime('%Y-%m-%d')
    except Exception:
        return datetime.now().strftime('%Y-%m-%d')

def list_all_folders(mail):
    """모든 폴더 목록 출력 및 반환"""
    _, folders = mail.list()
    folder_names = []
    print("\n📂 전체 메일함 목록:")
    for f in folders:
        try:
            decoded = f.decode("utf-8", errors="replace")
        except:
            decoded = str(f)
        print(f"  {decoded}")
        # 폴더 이름 추출 (마지막 구분자 이후)
        match = re.search(r'"([^"]+)"\s*$|(\S+)\s*$', decoded)
        if match:
            name = match.group(1) or match.group(2)
            folder_names.append(name)
    return folder_names

def try_select_folder(mail, keyword):
    """키워드로 폴더 찾아서 선택 시도"""
    _, folders = mail.list()
    for f in folders:
        try:
            raw = f.decode("utf-8", errors="replace")
        except:
            raw = str(f)

        if keyword in raw:
            # 폴더 이름 여러 방식으로 추출
            candidates = []

            # 방법1: 마지막 " " 사이
            m = re.findall(r'"([^"]*)"', raw)
            if m:
                candidates.append(m[-1])

            # 방법2: 마지막 공백 이후
            parts = raw.strip().split()
            if parts:
                candidates.append(parts[-1].strip('"'))

            # 각 후보로 select 시도
            for cand in candidates:
                for fmt in [f'"{cand}"', cand]:
                    try:
                        status, data = mail.select(fmt)
                        if status == 'OK':
                            print(f"✅ 폴더 선택 성공: {fmt}")
                            return True, int(data[0].decode())
                    except:
                        continue
    return False, 0

def main():
    print("=" * 50)
    print("  네이버 채용공고 메일 가져오기")
    print("=" * 50)
    password = getpass.getpass("애플리케이션 비밀번호 입력: ")

    print("\n📡 네이버 메일 연결 중...")
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(USERNAME, password)
        print("✅ 로그인 성공!")
    except Exception as e:
        print(f"❌ 로그인 실패: {e}")
        input("아무 키나 누르면 종료합니다.")
        return

    # 채용공고 폴더 직접 선택
    print(f"\n📂 채용공고 폴더 접속 중...")
    found = False
    total = 0
    for fmt in [f'"{JOB_FOLDER}"', JOB_FOLDER]:
        try:
            status, data = mail.select(fmt)
            if status == 'OK':
                found = True
                total = int(data[0].decode())
                print(f"✅ 폴더 선택 성공!")
                break
        except Exception as e:
            continue

    if not found:
        print("❌ 폴더 접근 실패. 프로그램을 종료합니다.")
        mail.logout()
        input("아무 키나 누르면 종료합니다.")
        return

    print(f"📧 총 {total}개 메일 발견")

    # 최근 100개 가져오기
    _, msg_ids = mail.search(None, 'ALL')
    id_list = msg_ids[0].split()
    recent = id_list[-100:] if len(id_list) > 100 else id_list
    print(f"🔄 최근 {len(recent)}개 처리 중...\n")

    jobs = []
    for i, eid in enumerate(reversed(recent)):
        try:
            _, msg_data = mail.fetch(eid, '(RFC822)')
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            subject = decode_str(msg['Subject'])
            sender  = decode_str(msg['From'])
            date    = parse_date(msg['Date'])
            body    = get_body(msg)

            company = re.sub(r'<[^>]+>', '', sender).replace('"', '').strip()
            if not company:
                company = sender.split('@')[0] if '@' in sender else sender

            channel = detect_channel(company, body)
            status  = auto_status(subject, body)
            job_url = extract_job_url(body)

            jobs.append({
                "id": f"email_{eid.decode()}_{int(datetime.now().timestamp()*1000)}",
                "createdAt": int(datetime.now().timestamp() * 1000) - i * 1000,
                "company":     company[:60],
                "position":    subject[:120],
                "deadline":    "",
                "appliedDate": "",
                "status":      status,
                "channel":     channel,
                "url":         job_url,
                "notes":       body,
            })

            if (i + 1) % 10 == 0:
                print(f"  ✔ {i+1}/{len(recent)} 처리됨")

        except Exception as e:
            print(f"  ⚠ 메일 {eid} 처리 오류: {e}")
            continue

    mail.logout()

    out_path = "jobs_import.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 완료! {len(jobs)}개 채용공고 → {out_path} 저장됨")
    print("\n📋 다음 단계:")
    print("  1. 브라우저에서 Daily Growth Hub 열기")
    print("  2. 취업 탭 → '📂 파일 선택' 버튼 클릭")
    print(f"  3. {out_path} 파일 선택하면 자동 등록!")
    input("\n아무 키나 누르면 종료합니다.")

if __name__ == "__main__":
    main()
