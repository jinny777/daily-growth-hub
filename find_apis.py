import urllib.request, ssl, re, json

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# groupby JS 청크에서 API 탐색
print("=== groupby.kr ===")
req = urllib.request.Request('https://groupby.kr/positions', headers=headers)
with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as r:
    html = r.read().decode('utf-8', errors='replace')

js_files = list(set(re.findall(r'/_next/static/chunks/[^\s"\']+\.js', html)))
for jf in js_files[:10]:
    try:
        req2 = urllib.request.Request(f'https://groupby.kr{jf}', headers=headers)
        with urllib.request.urlopen(req2, context=ssl_ctx, timeout=10) as r2:
            js = r2.read().decode('utf-8', errors='replace')
        hits = re.findall(r'"(/[a-z][^"\s]{5,60})"', js)
        job_hits = [h for h in hits if any(k in h.lower() for k in ['position','job','recruit'])]
        if job_hits:
            print(f"  {jf}:")
            for h in job_hits[:3]:
                print(f"    {h}")
    except Exception as e:
        pass

# remember API 탐색
print("\n=== career.rememberapp.co.kr ===")
req = urllib.request.Request('https://career.rememberapp.co.kr/job/postings', headers=headers)
with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as r:
    html2 = r.read().decode('utf-8', errors='replace')

js_files2 = list(set(re.findall(r'/_next/static/chunks/[^\s"\']+\.js', html2)))
for jf in js_files2[:10]:
    try:
        req2 = urllib.request.Request(f'https://career.rememberapp.co.kr{jf}', headers=headers)
        with urllib.request.urlopen(req2, context=ssl_ctx, timeout=10) as r2:
            js = r2.read().decode('utf-8', errors='replace')
        hits = re.findall(r'"(/[a-z][^"\s]{5,60})"', js)
        job_hits = [h for h in hits if any(k in h.lower() for k in ['job','posting','recruit','career'])]
        if job_hits:
            print(f"  {jf}:")
            for h in job_hits[:3]:
                print(f"    {h}")
    except:
        pass

# remember GraphQL 시도
print("\n=== remember GraphQL 시도 ===")
for ep in ['https://career.rememberapp.co.kr/graphql', 'https://api.rememberapp.co.kr/graphql']:
    try:
        body = json.dumps({"query": "{ jobPostings(page:1, limit:10) { id title company { name } } }"}).encode()
        req = urllib.request.Request(ep, data=body, headers={**headers, 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=8) as r:
            print(f"  {ep}: {r.read().decode('utf-8', errors='replace')[:200]}")
    except Exception as e:
        print(f"  실패 {ep}: {e}")
