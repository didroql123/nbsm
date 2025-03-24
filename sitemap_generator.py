import feedparser
from datetime import datetime
import html
import os
import re
from urllib.parse import quote

rss_url = "https://rss.blog.naver.com/rudtn668.xml"
base_url = "https://didroql123.github.io/nbsm"

print("📡 RSS 피드 로딩 중...")
feed = feedparser.parse(rss_url)
print(f"✅ 피드 로딩 완료, 글 수: {len(feed.entries)}")

os.makedirs("posts", exist_ok=True)
print("📁 'posts/' 폴더 준비 완료")

urls = [f"{base_url}/index.html"]
today = datetime.today().strftime('%Y-%m-%d')

index_html = "<h1>네이버 블로그 글 목록</h1>\n<ul>"

for i, entry in enumerate(feed.entries):
    print(f"🔹 글 {i+1}: {entry.title}")

    try:
        title = html.escape(entry.title)
        link = entry.link.replace("blog.naver.com", "m.blog.naver.com")
        date = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
        summary = entry.description if hasattr(entry, 'description') else "(요약 없음)"
        slug = re.sub(r"[^\w\s-]", "", entry.title)
        slug = re.sub(r"\s+", "-", slug).strip("-")

        # 개별 글 HTML 생성
        post_html = f"""<h2>{title}</h2>
<p><strong>작성일:</strong> {date}</p>
<p>{summary}</p>
<p><a href="{link}" target="_blank">🔗 네이버에서 보기</a></p>
"""
        post_path = f"posts/{slug}.html"
        with open(post_path, "w", encoding="utf-8") as f:
            f.write(post_html)
        print(f"✅ {post_path} 생성 완료")

        index_html += f'<li><a href="posts/{slug}.html">{title}</a></li>\n'
        urls.append(f"{base_url}/posts/{quote(slug)}.html")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

index_html += "</ul>"
with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_html)
print("✅ index.html 생성 완료")

# sitemap.xml 생성
sitemap = '''<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'''
for url in urls:
    sitemap += f"  <url><loc>{url}</loc><lastmod>{today}</lastmod></url>\n"
sitemap += "</urlset>"

with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap)
print("✅ sitemap.xml 생성 완료")

# robots.txt 생성
robots = f"""User-agent: *
Allow: /
Sitemap: {base_url}/sitemap.xml
"""

with open("robots.txt", "w", encoding="utf-8") as f:
    f.write(robots)
print("✅ robots.txt 생성 완료")
