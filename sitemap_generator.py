import feedparser
from datetime import datetime

# 네이버 블로그 RSS 주소 (본인의 RSS 주소로 교체)
rss_url = "https://rss.blog.naver.com/rudtn668.xml"

# RSS 피드 가져오기
feed = feedparser.parse(rss_url)

# XML Sitemap 구조
xml_template = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{}
</urlset>
'''

url_template = '''
  <url>
    <loc>{}</loc>
    <lastmod>{}</lastmod>
  </url>'''

urls = ''

# RSS의 각 글을 sitemap에 추가
for entry in feed.entries:
    url = entry.link
    lastmod = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
    urls += url_template.format(url, lastmod)

sitemap = xml_template.format(urls)

# sitemap.xml 저장
with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap)
