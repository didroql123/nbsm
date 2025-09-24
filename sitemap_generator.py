import feedparser
from datetime import datetime
import html
import os
import re
from urllib.parse import quote, urlparse
import codecs

# ▶ 두 RSS를 합쳐서 사용 (순서 무관)
FEEDS = [
    "https://rss.blog.naver.com/rudtn668.xml",  # 네이버 (주의: rss.blog.naver.com)
    "https://ksp668.tistory.com/rss",           # 티스토리
]

base_url = "https://didroql123.github.io/nbsm"
os.makedirs("posts", exist_ok=True)

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

# ✅ 모든 피드 수집 → 하나의 리스트로 병합
entries = []
for url in FEEDS:
    d = feedparser.parse(url)
    for e in d.entries:
        entries.append(e)

# ✅ 최신순 정렬
entries.sort(key=to_date, reverse=True)

# ✅ 메인 페이지 HTML 생성
index_html = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>경수 블로그 포스팅 리스트</title>
    <style>
        body { font-family: sans-serif; background: #f9f9f9; padding: 2em; max-width: 900px; margin: auto; }
        .card { background: white; padding: 1.5em; margin-bottom: 1.5em; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
        .card-title { font-size: 1.3em; font-weight: bold; margin-bottom: 0.5em; }
        .card-date { color: #888; font-size: 0.9em; margin-bottom: 0.8em; }
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
    if src == "네이버":
        link = html.escape(link_raw.replace("blog.naver.com", "m.blog.naver.com"))
    else:
        link = html.escape(link_raw)

    dt = to_date(entry)
    date = dt.strftime("%Y-%m-%d")

    # summary/description 사용 (있으면)
    summary = getattr(entry, "description", None)
    summary = summary if summary else "(요약 없음)"

    # 동일 제목 충돌 방지를 위해 날짜/출처 프리픽스 섞어 슬러그 생성
    slug_base = slugify(getattr(entry, "title", "post"))
    slug = f"{dt.strftime('%Y%m%d')}-{src}-{slug_base}"

    page_url = f"{base_url}/posts/{quote(slug)}.html"
    urls.append(page_url)

    # ▶ 상세 페이지 (버튼 문구: 출처에 따라 변경)
    btn_text = f"{src} 블로그에서 전체 글 보기"
    post_html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: sans-serif; max-width: 800px; margin: auto; padding: 2em; }}
        .title {{ font-size: 1.8em; font-weight: bold; margin-bottom: 0.5em; }}
        .meta {{ color: #777; margin-bottom: 1em; }}
        .summary {{ font-size: 1em; color: #333; margin-bottom: 2em; }}
        .badge {{ display:inline-block; font-size: 0.85em; padding: 2px 8px; border-radius: 999px; background:#eef; margin-right:8px; }}
        a.button {{ background: #0077cc; color: white; padding: 0.6em 1em; text-decoration: none; border-radius: 6px; }}
        a.button:hover {{ background: #005fa3; }}
    </style>
</head>
<body>
    <div class="title">{title}</div>
    <div class="meta"><span class="badge">{src}</span>🗓 {date}</div>
    <div class="summary">{summary}</div>
    <a class="button" href="{link}" target="_blank" rel="noopener">{btn_text}</a>
</body>
</html>
'''
    with open(f"posts/{slug}.html", "w", encoding="utf-8") as f:
        f.write(post_html)

    # ✅ 메인에 카드 추가 (출처 뱃지 + 상세 보기)
    index_html += f'''
    <div class="card">
        <div class="card-title"><span class="badge">{src}</span><a href="posts/{slug}.html">{title}</a></div>
        <div class="card-date">🗓 {date}</div>
        <div class="card-summary">{summary}</div>
        <div class="card-link">
            <a href="posts/{slug}.html">상세 보기</a>
        </div>
    </div>
    '''

index_html += '</body></html>'
with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_html)

# ✅ sitemap.xml 생성
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

# ✅ robots.txt 생성
robots_txt = f"""User-agent: *
Allow: /
Sitemap: {base_url}/sitemap.xml
"""

with codecs.open("robots.txt", "w", encoding="utf-8") as f:
    f.write(robots_txt)
