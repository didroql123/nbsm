import feedparser
from datetime import datetime
import html
import os
import re
from urllib.parse import quote

rss_url = "https://blog.rss.naver.com/rudtn668.xml"
base_url = "https://didroql123.github.io/nbsm"

feed = feedparser.parse(rss_url)
os.makedirs("posts", exist_ok=True)

# ✅ 메인 페이지 HTML 생성
index_html = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>네이버 블로그 포스팅 리스트</title>
    <style>
        body { font-family: sans-serif; background: #f9f9f9; padding: 2em; max-width: 900px; margin: auto; }
        .card { background: white; padding: 1.5em; margin-bottom: 1.5em; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
        .card-title { font-size: 1.3em; font-weight: bold; margin-bottom: 0.5em; }
        .card-date { color: #888; font-size: 0.9em; margin-bottom: 0.8em; }
        .card-summary { font-size: 1em; color: #333; margin-bottom: 1em; }
        .card-link a { background: #0077cc; color: white; padding: 0.5em 1em; text-decoration: none; border-radius: 6px; font-size: 0.95em; }
        .card-link a:hover { background: #005fa3; }
    </style>
</head>
<body>
    <h1>네이버 블로그 최신 글 모음</h1>
'''

def slugify(text):
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text.strip("-")

urls = [f"{base_url}/index.html"]
today = datetime.today().strftime('%Y-%m-%d')

for entry in feed.entries:
    title = html.escape(entry.title)
    link = html.escape(entry.link.replace("blog.naver.com", "m.blog.naver.com"))
    date = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
    summary = html.escape(entry.summary) if "summary" in entry else "(요약 없음)"
    slug = slugify(entry.title)
    page_url = f"{base_url}/posts/{quote(slug)}.html"
    urls.append(page_url)

    # ✅ 상세 페이지 생성
    post_html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: sans-serif; max-width: 800px; margin: auto; padding: 2em; }}
        .title {{ font-size: 1.8em; font-weight: bold; margin-bottom: 0.5em; }}
        .date {{ color: #777; margin-bottom: 1em; }}
        .summary {{ font-size: 1em; color: #333; margin-bottom: 2em; }}
        a.button {{ background: #0077cc; color: white; padding: 0.6em 1em; text-decoration: none; border-radius: 6px; }}
        a.button:hover {{ background: #005fa3; }}
    </style>
</head>
<body>
    <div class="title">{title}</div>
    <div class="date">🗓 {date}</div>
    <div class="summary">{summary}</div>
    <a class="button" href="{link}" target="_blank">네이버 블로그에서 전체 글 보기</a>
</body>
</html>
'''
    with open(f"posts/{slug}.html", "w", encoding="utf-8") as f:
        f.write(post_html)

    # ✅ 메인에 카드 추가
    index_html += f'''
    <div class="card">
        <div class="card-title"><a href="posts/{slug}.html">{title}</a></div>
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

with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_xml)

# ✅ robots.txt 생성
robots_txt = f"""User-agent: *
Allow: /
Sitemap: {base_url}/sitemap.xml
"""

with open("robots.txt", "w", encoding="utf-8") as f:
    f.write(robots_txt)
