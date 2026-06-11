"""
뉴스클리핑 자동 수집 스크립트
- Google 뉴스 RSS에서 카테고리별 키워드로 검색
- sync-data.json 의 newsCategories 설정을 우선 사용 (없으면 기본 카테고리 사용)
실행: python news_fetch.py
"""
import urllib.request
import urllib.parse
import json
import re
import time
import ssl
import xml.etree.ElementTree as ET

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

# 프론트엔드(NEWS_DEFAULT_CATS)와 동일한 기본 카테고리
NEWS_DEFAULT_CATS = [
    {'id': 'nc_ai',      'name': 'AI/기술',     'color': 'indigo', 'keywords': ['인공지능', 'AI', '챗GPT', 'LLM']},
    {'id': 'nc_startup', 'name': '창업/스타트업', 'color': 'green',  'keywords': ['스타트업', '창업', '유니콘', '벤처투자']},
    {'id': 'nc_economy', 'name': '경제/금융',    'color': 'orange', 'keywords': ['금리', '주식', '경제', '투자']},
    {'id': 'nc_global',  'name': '글로벌',      'color': 'blue',   'keywords': ['글로벌', '해외진출', '수출', '미국']},
]

ARTICLES_PER_CATEGORY = 20


def fetch(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*',
    })
    try:
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=20) as res:
            return res.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  ⚠ 요청 실패: {e}")
        return None


def strip_html_tags(s):
    s = re.sub(r'<[^>]*>', '', s or '')
    s = (s.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<')
           .replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'"))
    return re.sub(r'\s+', ' ', s).strip()


def extract_source_from_title(title):
    m = re.search(r'-\s*([^-]+)$', title)
    return m.group(1).strip() if m else ''


def find_matching_keyword(text, keywords):
    text_lower = text.lower()
    for kw in keywords:
        if kw and kw.lower() in text_lower:
            return kw
    return keywords[0] if keywords else ''


def parse_rss(xml_text):
    items = []
    try:
        root = ET.fromstring(xml_text)
    except Exception as e:
        print(f"  ⚠ XML 파싱 실패: {e}")
        return items
    channel = root.find('channel')
    if channel is None:
        return items
    for item in channel.findall('item'):
        source_el = item.find('source')
        items.append({
            'title':       item.findtext('title') or '',
            'link':        item.findtext('link') or '',
            'pubDate':     item.findtext('pubDate') or '',
            'description': item.findtext('description') or '',
            'source':      (source_el.text or '').strip() if source_el is not None else '',
        })
    return items


def fetch_news_for_category(cat):
    keywords = cat.get('keywords') or []
    if not keywords:
        return []
    query = ' OR '.join(keywords)
    rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=ko&gl=KR&ceid=KR:ko"
    print(f"📡 '{cat.get('name')}' 뉴스 수집 중... (검색어: {query})")

    data = fetch(rss_url)
    if not data:
        return []

    seen = set()
    articles = []
    for raw in parse_rss(data):
        link = raw['link'].strip()
        if not link or link in seen:
            continue
        seen.add(link)
        title = strip_html_tags(raw['title'])
        description = strip_html_tags(raw['description'])
        source = raw['source'] or extract_source_from_title(raw['title'])
        articles.append({
            'title':       title,
            'link':        link,
            'pubDate':     raw['pubDate'].strip(),
            'description': description,
            'source':      source,
            'keyword':     find_matching_keyword(title + ' ' + description, keywords),
            'catId':       cat['id'],
        })
        if len(articles) >= ARTICLES_PER_CATEGORY:
            break

    print(f"  → {len(articles)}건 수집")
    return articles


def load_categories():
    """sync-data.json 에 사용자가 설정한 카테고리가 있으면 그걸 사용, 없으면 기본값"""
    try:
        with open('sync-data.json', encoding='utf-8') as f:
            data = json.load(f)
        cats = data.get('state', {}).get('newsCategories')
        if cats:
            print(f"📂 sync-data.json 에서 카테고리 {len(cats)}개 로드")
            return cats
    except Exception as e:
        print(f"  ⚠ sync-data.json 로드 실패, 기본 카테고리 사용: {e}")
    return NEWS_DEFAULT_CATS


def main():
    print("=" * 50)
    print("  뉴스클리핑 자동 수집")
    print("=" * 50)

    categories = load_categories()
    result = {'fetchedAt': int(time.time() * 1000), 'categories': {}}

    total = 0
    for cat in categories:
        articles = fetch_news_for_category(cat)
        result['categories'][cat['id']] = {'name': cat.get('name', ''), 'articles': articles}
        total += len(articles)

    out_path = 'news_clipping.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 총 {total}건 수집 → {out_path} 저장 완료!")


if __name__ == '__main__':
    main()
