# -*- coding: utf-8 -*-
import feedparser
import requests, time, random
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import html, os, re, glob
from urllib.parse import quote, urlparse

# ===== 설정 =====
FEEDS = [
    "https://rss.blog.naver.com/rudtn668.xml",  # 네이버
    "https://ksp668.tistory.com/rss",           # 티스토리
    "https://rss.blog.naver.com/syslogbook.xml"
]

base_url = "https://didroql123.github.io/nbsm"
SUMMARY_LEN = 160
GUARD_SOURCES = []  # 머지 모드를 쓰므로 가드로 스킵하지 않음(원하면 ["네이버"] 등으로)

# ===== 유틸 =====
TAG_RE = re.compile(r"<[^>]+>")
WS_RE  = re.compile(r"\s+")
TITLE_RE   = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
SUMMARYDIV = re.compile(r'<div class="summary">(.*?)</div>', re.IGNORECASE | re.DOTALL)
FNAME_RE   = re.compile(r"(\d{8})-([^-]+)-(.+)\.html$")  # YYYYMMDD-출처-슬러그.html

def strip_tags(html_text: str) -> str:
    text = TAG_RE.sub(" ", html_text or "")
    text = html.unescape(text)
    text = WS_RE.sub(" ", text).strip()
    return text

def slugify(text):
    text = re.sub(r"[^\w\s-]", "", text or "post")
    text = re.sub(r"\s+", "-", text)
    return text.strip("-")

def src_label(link: str) -> str:
    host = (urlparse(link).hostname or "").lower()
    if "tistory.com" in host: return "티스토리"
    if "naver.com"   in host: return "네이버"  # blog.naver.com, m.blog.naver.com, post.naver.com 등
    return "기타"

def to_date(entry) -> datetime:
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        val = getattr(entry, key, None)
        if val:
            return datetime(*val[:6])
    for key in ("published", "updated"):
        s = getattr(entry, key, None)
        if s:
            try:
                return parsedate_to_datetime(s)
            except Exception:
                pass
    return datetime.utcnow()

# ===== 네이버 안정화: requests로 바이트 가져와 feedparser에 넘김 =====
SESSION = requests.Session()
DEFAULT_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36"),
    "Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.7",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://blog.naver.com/",
    "Connection": "close",
}

def fetch_bytes(url: str, timeout=15, max_retry=3, backoff=2.0) -> bytes:
    last_err = None
    for i in range(max_retry):
        try:
            if "naver.com" in url:  # 네이버는 특히 헤더 중요
                time.sleep(random.uniform(0.8, 1.6))  # 요청 간 간격
            resp = SESSION.get(url, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=True)
            if 200 <= resp.status_code < 300 and resp.content:
                return resp.content
            last_err = f"HTTP {resp.status_code}"
        except requests.RequestException as e:
            last_err = str(e)
        time.sleep(backoff * (i+1) + random.uniform(0, 0.6))
    raise RuntimeError(f"Fetch failed: {url} ({last_err})")

def parse_feed(url: str):
    raw = fetch_bytes(url)
    d = feedparser.parse(raw)
    print(f"[FEED] {url} -> entries={len(getattr(d,'entries',[]))} bozo={getattr(d,'bozo',None)}")
    if getattr(d, "bozo", 0):
        print("bozo_exception:", getattr(d, "bozo_exception", None))
    return d

# ===== 데이터 수집 =====
entries = []
for url in FEEDS:
    try:
        d = parse_feed(url)
        entries.extend(d.entries)
    except Exception as e:
        print("[ERROR] feed fetch/parse:", url, e)

# 최신순
entries.sort(key=to_date, reverse=True)

# ===== posts 생성 (원문 HTML 최대 유지) =====
os.makedirs("posts", exist_ok=True)

def extract_summary(entry) -> tuple[str, str]:
    full_html = None
    if getattr(entry, "content", None) and len(entry.content) > 0 and getattr(entry.content[0], "value", None):
        full_html = entry.content[0].value
    elif hasattr(entry, "description"):
        full_html = entry.description
    elif hasattr(entry, "summary"):
        full_html = entry.summary
    if not full_html:
        return "(요약 없음)", "(요약 없음)"
    short = strip_tags(full_html)
    if len(short) > SUMMARY_LEN:
        short = short[:SUMMARY_LEN].rstrip() + "…"
    return short, full_html

today_iso = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
urls = [f"{base_url}/index.html"]
src_counts = {"네이버": 0, "티스토리": 0, "기타": 0}

for entry in entries:
    title_txt = getattr(entry, "title", "(제목 없음)")
    title = html.escape(title_txt)
    link_raw = getattr(entry, "link", "#")
    src = src_label(link_raw)

    # 네이버 링크 모바일로
    link = link_raw.replace("blog.naver.com", "m.blog.naver.com") if src == "네이버" else link_raw
    link = html.escape(link)

    dt = to_date(entry)
    date_str = dt.strftime("%Y-%m-%d")

    short_summary, detail_summary_html = extract_summary(entry)
    short_summary_escaped = html.escape(short_summary)

    slug_base = slugify(title_txt)
    slug = f"{dt.strftime('%Y%m%d')}-{src}-{slug_base}"
    page_url = f"{base_url}/posts/{quote(slug)}.html"
    urls.append(page_url)

    post_html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <meta name="robots" content="index,follow">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; max-width: 800px; margin: auto; padding: 2em; }}
    .title {{ font-size: 1.8em; font-weight: 800; margin-bottom: 0.5em; }}
    .meta {{ color: #777; margin-bottom: 1em; }}
    .summary {{ font-size: 1em; color: #333; margin-bottom: 2em; }}
    .badge {{ display:inline-block; font-size: 0.85em; padding: 2px 8px; border-radius: 999px; background:#eef; margin-right:8px; }}
    .summary img {{ max-width: 100%; height: auto; }}
    a.button {{ background: #0077cc; color: white; padding: 0.6em 1em; text-decoration: none; border-radius: 6px; }}
    a.button:hover {{ background: #005fa3; }}
  </style>
</head>
<body>
  <div class="title">{title}</div>
  <div class="meta"><span class="badge">{src}</span>🗓 {date_str}</div>
  <div class="summary">{detail_summary_html}</div>
  <a class="button" href="{link}" target="_blank" rel="noopener">{src} 블로그에서 전체 글 보기</a>
</body>
</html>
'''
    with open(f"posts/{slug}.html", "w", encoding="utf-8") as f:
        f.write(post_html)

    src_counts[src] = src_counts.get(src, 0) + 1

print("[SRC COUNTS]", src_counts)

# ===== 머지 모드: posts/ 스캔해 index/sitemaps 재구성 (피드 0건 대비)
def scan_posts_for_index(base_url: str, summary_len: int = 160):
    items = []
    for path in glob.glob("posts/*.html"):
        fname = os.path.basename(path)
        m = FNAME_RE.match(fname)
        if not m:
            continue
        ymd, src, _ = m.groups()
        date_str = f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}"
        with open(path, "r", encoding="utf-8") as f:
            html_text = f.read()
        t = TITLE_RE.search(html_text)
        title = html.escape(strip_tags(t.group(1))) if t else "(제목 없음)"
        s = SUMMARYDIV.search(html_text)
        detail_html = s.group(1) if s else ""
        short = strip_tags(detail_html)
        if len(short) > summary_len:
            short = short[:summary_len].rstrip() + "…"
        items.append({
            "src": src,
            "title": title,
            "date_str": date_str,
            "href": f"posts/{fname}",
            "short": html.escape(short),
            "abs_url": f"{base_url}/posts/{quote(fname)}"
        })
    # 파일명 기준 역순(YYYYMMDD가 앞에)
    items.sort(key=lambda x: x["href"], reverse=True)
    return items

# 인덱스 카드 데이터 만들기:
# - 기본: 이번 실행에서 수집한 entries
# - 보강: 혹시 피드가 0건인 출처가 있더라도 posts/에서 보충
def build_cards_from_entries(entries):
    cards = []
    for entry in entries:
        title_txt = getattr(entry, "title", "(제목 없음)")
        title = html.escape(title_txt)
        link_raw = getattr(entry, "link", "#")
        src = src_label(link_raw)
        dt = to_date(entry); date_str = dt.strftime("%Y-%m-%d")
        short_summary, _detail = extract_summary(entry)
        short_summary_escaped = html.escape(short_summary)
        slug = f"{dt.strftime('%Y%m%d')}-{src}-{slugify(title_txt)}"
        cards.append({
            "src": src,
            "title": title,
            "date_str": date_str,
            "href": f"posts/{slug}.html",
            "short": short_summary_escaped
        })
    # 최신순
    cards.sort(key=lambda x: x["href"], reverse=True)
    return cards

cards = build_cards_from_entries(entries)

# 피드가 비어서 카드가 부족하면 posts/ 스캔으로 대체/보강
if not cards or any(src_counts.get(s, 0) == 0 for s in ("네이버", "티스토리")):
    print("[MERGE] Using posts/ scan to (re)build index to avoid empty sources.")
    scanned = scan_posts_for_index(base_url, SUMMARY_LEN)
    if scanned:  # posts에 뭔가라도 있으면 그것으로 인덱스 구성
        cards = scanned
        # sitemap URLs도 posts 기반으로 재구성
        urls = [f"{base_url}/index.html"] + [it["abs_url"] for it in scanned]

# ===== index.html 생성 =====
index_html = '''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>경수 블로그 최신 글 모음</title>
  <meta name="description" content="네이버/티스토리 최신글 요약">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; background: #f9f9f9; padding: 2em; max-width: 900px; margin: auto; }
    .card { background: white; padding: 1.5em; margin-bottom: 1.5em; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .card-title { font-size: 1.3em; font-weight: 700; margin-bottom: 0.5em; }
    .card-title a { color: #111; text-decoration: none; }
    .card-date { color: #888; font-size: 0.9em; margin-bottom: 0.6em; }
    .badge { display:inline-block; font-size: 0.8em; padding: 2px 8px; border-radius: 999px; background:#eef; margin-right:8px; }
    .card-summary { font-size: 1em; color: #333; margin-bottom: 1em; }
    .card-link a { background: #0077cc; color: white; padding: 0.5em 1em; text-decoration: none; border-radius: 6px; font-size: 0.95em; }
    .card-link a:hover { background: #005fa3; }
  </style>
</head>
<body>
  <h1>경수 블로그 최신 글 모음</h1>
'''

for it in cards:
    index_html += f'''
  <div class="card">
    <div class="card-title"><span class="badge">{it["src"]}</span><a href="{it["href"]}">{it["title"]}</a></div>
    <div class="card-date">🗓 {it["date_str"]}</div>
    <div class="card-summary">{it["short"]}</div>
    <div class="card-link">
      <a href="{it["href"]}">상세 보기</a>
    </div>
  </div>
'''

index_html += '</body></html>'
with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_html)

# ===== Sitemaps =====
def build_sitemap(url_list):
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in url_list:
        out += [
            '  <url>',
            f'    <loc>{u}</loc>',
            f'    <lastmod>{today_iso}</lastmod>',
            '  </url>'
        ]
    out.append('</urlset>')
    return "\n".join(out)

sitemap_main = build_sitemap(urls)
with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_main)
with open("sitemap-1.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_main)

sitemap_index = f'''<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>{base_url}/sitemap.xml</loc>
    <lastmod>{today_iso}</lastmod>
  </sitemap>
  <sitemap>
    <loc>{base_url}/sitemap-1.xml</loc>
    <lastmod>{today_iso}</lastmod>
  </sitemap>
</sitemapindex>
'''
with open("sitemap_index.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_index)

# ===== robots.txt =====
robots_txt = f"""User-agent: *
Allow: /
Sitemap: {base_url}/sitemap.xml
Sitemap: {base_url}/sitemap-1.xml
Sitemap: {base_url}/sitemap_index.xml
"""
with open("robots.txt", "w", encoding="utf-8") as f:
    f.write(robots_txt)

print("Generated: index.html, posts/*.html, sitemap.xml, sitemap-1.xml, sitemap_index.xml, robots.txt")
