import feedparser
from datetime import datetime
import html

rss_url = "https://blog.rss.naver.com/rudtn668.xml"
feed = feedparser.parse(rss_url)

html_output = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>경수 네이버 블로그 최신 글 모음</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background: #f9f9f9;
            padding: 2em;
            max-width: 900px;
            margin: auto;
        }
        .card {
            background: white;
            padding: 1.5em;
            margin-bottom: 1.5em;
            border-radius: 12px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        }
        .card-title {
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 0.5em;
        }
        .card-date {
            color: #888;
            font-size: 0.9em;
            margin-bottom: 0.8em;
        }
        .card-summary {
            font-size: 1em;
            color: #333;
            margin-bottom: 1em;
        }
        .card-link a {
            background: #0077cc;
            color: white;
            padding: 0.5em 1em;
            text-decoration: none;
            border-radius: 6px;
            font-size: 0.95em;
        }
        .card-link a:hover {
            background: #005fa3;
        }
    </style>
</head>
<body>
    <h1>네이버 블로그 최신 글 모음</h1>
'''

for entry in feed.entries:
    title = html.escape(entry.title)
    link = html.escape(entry.link.replace("blog.naver.com", "m.blog.naver.com"))
    date = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
    summary = html.escape(entry.summary) if "summary" in entry else "(요약 없음)"

    html_output += f'''
    <div class="card">
        <div class="card-title">{title}</div>
        <div class="card-date">🗓 {date}</div>
        <div class="card-summary">{summary}</div>
        <div class="card-link">
            <a href="{link}" target="_blank">네이버 블로그 글 보기</a>
        </div>
    </div>
    '''

html_output += '''
</body>
</html>
'''

# ✅ 저장 파일명을 index.html로!
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_output)
