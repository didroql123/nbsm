import feedparser
from datetime import datetime, timezone
import html
import os
import re
from urllib.parse import quote, urlparse
import codecs

# ===== 설정 =====
# 네이버 + 티스토리 RSS 둘 다 합칩니다.
FEEDS = [
    "https://rss.blog.naver.com/rudtn668.xml",  # 네이버
    "https://ksp668.tistory.com/rss",           # 티스토리
]

# GitHub Pages 배포 경로(네 페이지의 퍼블릭 URL prefix)
base_url = "https://didroql123.github.io/nbsm"

# 인덱스 카드 요약 최대 길이
SUMMARY_LEN = 160

# ===== 유틸 =====
TAG_RE = re.compile(r"<[^>]+>")
WS_RE  = re.compile(r"\s+")

def strip_tags(html_text: str) -> str:
    text = TAG_RE.sub(" ", html_text or "")
    text = html.unescape(text)
    text = WS_RE.sub(" ", text).strip()
    return text

def extract_summary(entry) -> tuple[str, str]:
    """
    반환: (index용_짧은_요약, detail용_원문HTML_or텍스트)
    우선순위: content:encoded > description > summary
    """
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

def src_label(link: str) -> str:
    host = (urlparse(link).hostname or "").lower()
    if "tistory.com" in host: return "티스토리"
    if "naver.com" in host:   return "네이버"
    return "기타"

def to_date(entry) -> datetime:
    if getattr(entry, "published_parsed", None):
        return datetime(*entry.published_parsed[:6])
    if getattr(entry, "updated_parsed", None):
        return datetime(*entry.updated_parsed[:6])
    return datetime.utcnow()

def slugify(text):
    text = re.sub(r"[^\w\s-]", "", text or "post")
    text = re.sub(r"\s+", "-", text)
    return text.strip("-")

# ===== 데이터 수집 =====
entries = []
for url in FEEDS:
    d = feedparser.parse(url)
    for e in d.entries:
        entries.append(e)

# 최신순
entries.sort(key=to_date, reverse=True)

# 출력 폴더
os.makedirs("posts", exist_ok=True)

# ===== index.html 생성 (요약 표시) =====
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

urls = [f"{base_url}/index.html"]
today_iso = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

for entry in entries:
    title = html.escape(getattr(entry, "title", "(제목 없음)"))
    link_raw = getattr(entry, "link", "#")
    src = src_label(link_raw)

    # 네이버는 모바일 링크로 교체(가독성)
    link = link_raw.replace("blog.naver.com", "m.blog.naver.com") if src == "네이버" else link_raw
    link = html.escape(link)

    dt = to_date(entry)
    date_str = dt.strftime("%Y-%m-%d")

    short_summary, detail_summary_html = extract_summary(entry)
    short_summary_escaped = html.escape(short_summary)

    # 충돌 방지용 슬러그: YYYYMMDD-출처-제목
    slug_base = slugify(getattr(entry, "title", "post"))
    slug = f"{dt.strftime('%Y%m%d')}-{src}-{slug_base}"
    page_url = f"{base_url}/posts/{quote(slug)}.html"
    urls.append(page_url)

    # 상세 페이지 생성(원문 HTML 최대한 유지)
    btn_text = f"{src} 블로그에서 전체 글 보기"
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
  <a class="button" href="{link}" target="_blank" rel="noopener">{btn_text}</a>
</body>
</html>
'''
    with open(f"posts/{slug}.html", "w", encoding="utf-8") as f:
        f.write(post_html)

    # index 카드(짧은 요약)
    index_html += f'''
  <div class="card">
    <div class="card-title"><span class="badge">{src}</span><a href="posts/{slug}.html">{title}</a></div>
    <div class="card-date">🗓 {date_str}</div>
    <div class="card-summary">{short_summary_escaped}</div>
    <div class="card-link">
      <a href="posts/{slug}.html">상세 보기</a>
    </div>
  </div>
'''

index_html += '</body></html>'
with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_html)

# ===== Sitemaps =====
def build_sitemap(url_list: list[str]) -> str:
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

# 기본 사이트맵
sitemap_main = build_sitemap(urls)
with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_main)

# 캐시 우회용 새 파일명(권장)
with open("sitemap-1.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_main)

# 사이트맵 인덱스(두 개를 참조)
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
