import feedparser
from datetime import datetime
import html
import os
import re
from urllib.parse import quote, urlparse
import codecs

# ▶ 두 RSS를 합쳐 사용
FEEDS = [
    "https://rss.blog.naver.com/rudtn668.xml",  # 네이버
    "https://ksp668.tistory.com/rss",           # 티스토리
]

base_url = "https://didroql123.github.io/nbsm"
os.makedirs("posts", exist_ok=True)

# ===== 요약 관련 유틸 =====
SUMMARY_LEN = 160  # 인덱스 카드에 보여줄 요약 길이

TAG_RE = re.compile(r"<[^>]+>")
WS_RE  = re.compile(r"\s+")

def strip_tags(html_text: str) -> str:
    # 태그 제거 + 공백 정리
    text = TAG_RE.sub(" ", html_text or "")
    text = html.unescape(text)
    text = WS_RE.sub(" ", text).strip()
    return text

def extract_summary(entry) -> tuple[str, str]:
    """
    반환: (index용_짧은_요약, detail용_전체_요약_HTML)
    - index용: 태그 제거 + 길이 제한
    - detail용: 원문 HTML(가능하면) 또는 텍스트
    우선순위: content:encoded > description > summary
    """
    full_html = None
    # content:encoded (feedparser에선 entry.content[0].value 인 경우 많음)
    if getattr(entry, "content", None) and len(entry.content) > 0 and getattr(entry.content[0], "value", None):
        full_html = entry.content[0].value
    elif hasattr(entry, "description"):
        full_html = entry.description
    elif hasattr(entry, "summary"):
        full_html = entry.summary

    if not full_html:
        return "(요약 없음)", "(요약 없음)"

    # index용: 태그 제거 + 길이 제한
    text = strip_tags(full_html)
    if len(text) > SUMMARY_LEN:
        text = text[:SUMMARY_LEN].rstrip() + "…"

    # detail용: 원문 HTML을 그대로 쓰되, 너무 지저분하면 텍스트로 대체해도 됨
    detail_html = full_html
    return text, detail_html

# ===== 기타 유틸 =====
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
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text.strip("-")

# ===== 피드 수집 & 정렬 =====
entries = []
for url in FEEDS:
    d = feedparser.parse(url)
    for e in d.entries:
        entries.append(e)
entries.sort(key=to_date, reverse=True)

# ===== index.html 생성 (요약 표시) =====
index_html = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>경수 블로그 최신 글 모음</title>
    <meta name="description" content="네이버/티스토리 최신글 요약">
    <style>
        body { font-family: sans-serif; background: #f9f9f9; padding: 2em; max-width: 900px; margin: auto; }
        .card { background: white; padding: 1.5em; margin-bottom: 1.5em; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
        .card-title { font-size: 1.3em; font-weight: bold; margin-bottom: 0.5em; }
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
today = datetime.today().strftime('%Y-%m-%d')

for entry in entries:
    title = html.escape(getattr(entry, "title", "(제목 없음)"))
    link_raw = getattr(entry, "link", "#")
    src = src_label(link_raw)

    # 네이버는 모바일 링크로 교체(가독성)
    link = link_raw.replace("blog.naver.com", "m.blog.naver.com") if src == "네이버" else link_raw
    link = html.escape(link)

    dt = to_date(entry)
    date = dt.strftime("%Y-%m-%d")

    # ★ index용 요약 + detail용 요약 추출
    short_summary, detail_summary_html = extract_summary(entry)
    short_summary_escaped = html.escape(short_summary)

    # 동일 제목 충돌 방지: 날짜/출처 포함
    slug_base = slugify(getattr(entry, "title", "post"))
    slug = f"{dt.strftime('%Y%m%d')}-{src}-{slug_base}"

    page_url = f"{base_url}/posts/{quote(slug)}.html"
    urls.append(page_url)

    # ===== 상세 페이지 생성 (detail_summary_html은 원문 HTML 유지) =====
    btn_text = f"{src} 블로그에서 전체 글 보기"
    post_html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <meta name="robots" content="index,follow">
    <style>
        body {{ font-family: sans-serif; max-width: 800px; margin: auto; padding: 2em; }}
        .title {{ font-size: 1.8em; font-weight: bold; margin-bottom: 0.5em; }}
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
    <div class="meta"><span class="badge">{src}</span>🗓 {date}</div>
    <div class="summary">{detail_summary_html}</div>
    <a class="button" href="{link}" target="_blank" rel="noopener">{btn_text}</a>
</body>
</html>
'''
    with open(f"posts/{slug}.html", "w", encoding="utf-8") as f:
        f.write(post_html)

    # ===== index 카드 (★ 요약은 짧게 표시) =====
    index_html += f'''
    <div class="card">
        <div class="card-title"><span class="badge">{src}</span><a href="posts/{slug}.html">{title}</a></div>
        <div class="card-date">🗓 {date}</div>
        <div class="card-summary">{short_summary_escaped}</div>
        <div class="card-link">
            <a href="posts/{slug}.html">상세 보기</a>
        </div>
    </div>
    '''

index_html += '</body></html>'
with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_html)

# ===== sitemap.xml =====
sitemap_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
'''
for url in urls:
    sitemap_xml += f'''
  <url>
    <loc>{url}</loc>
    <lastmod>{today}</lastmod>
  </url>'''
sitemap_xml += '\n</urlset>'

with codecs.open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_xml)

# ===== robots.txt =====
robots_txt = f"""User-agent: *
Allow: /
Sitemap: {base_url}/sitemap.xml
"""

with codecs.open("robots.txt", "w", encoding="utf-8") as f:
    f.write(robots_txt)
