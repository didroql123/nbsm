import feedparser
import html
from datetime import datetime

rss_url = "https://blog.rss.naver.com/rudtn668.xml"
feed = feedparser.parse(rss_url)

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

for entry in feed.entries:
    url = html.escape(entry.link)  # ← 여기!
    lastmod = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
    urls += url_template.format(url, lastmod)

sitemap = xml_template.format(urls)

with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap)
