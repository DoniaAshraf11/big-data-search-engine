import asyncio
import aiohttp
from selectolax.parser import HTMLParser
from urllib.parse import urljoin, urlparse
import re
import json
import time

URLS_FILE = 'urls.txt'
CONCURRENCY = 50                # عدد العُمال المتزامنين
MAX_TOTAL_PAGES = 10000         # الهدف النهائي لعدد الصفحات
MAX_LINKS_PER_PAGE = 200        # روابط فرعية لكل صفحة
CONTENT_MIN_LENGTH = 20
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def load_urls(file_path):
    with open(file_path, encoding='utf-8') as f:
        return [l.strip() for l in f if l.strip()]

def extract_content(html):
    tree = HTMLParser(html)
    for node in tree.css('script, style, nav, footer, iframe'):
        node.decompose()
    parts = [n.text(strip=True) for n in tree.css('p,h1,h2,h3') if n.text(strip=True)]
    text = ' '.join(parts)
    return re.sub(r'\s+', ' ', text)

async def fetch(session, url):
    try:
        async with session.get(url, headers=HEADERS, timeout=10) as resp:
            resp.raise_for_status()
            return await resp.text()
    except:
        return None

async def worker(name, session, queue, visited, articles, meta):
    while True:
        url = await queue.get()
        if url in visited or len(visited) >= MAX_TOTAL_PAGES:
            queue.task_done()
            continue
        html = await fetch(session, url)
        visited.add(url)
        if html:
            content = extract_content(html)
            if len(content) >= CONTENT_MIN_LENGTH:
                # استخراج العنوان
                m = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
                title = m.group(1).strip() if m else url
                articles.append({"url": url, "title": title, "content": content})
                meta[url] = {
                    "url": url, "title": title,
                    "content_length": len(content), "pagerank": 1.0
                }
                # جمع الروابط الفرعية
                tree = HTMLParser(html)
                count = 0
                for a in tree.css('a[href]'):
                    href = a.attributes['href']
                    full = urljoin(url, href)
                    if (urlparse(full).netloc == urlparse(url).netloc
                        and not full.lower().endswith(('.pdf','.jpg','.png','.mp4','.mp3'))):
                        if full not in visited:
                            await queue.put(full)
                            count += 1
                    if count >= MAX_LINKS_PER_PAGE:
                        break
        queue.task_done()

async def scrape_all(seeds):
    queue = asyncio.Queue()
    for u in seeds:
        await queue.put(u)

    visited = set()
    articles = []
    meta = {}

    async with aiohttp.ClientSession() as session:
        workers = [
            asyncio.create_task(worker(f"w{i}", session, queue, visited, articles, meta))
            for i in range(CONCURRENCY)
        ]
        # انتظر استنفاد الطابور أو الوصول للحد
        await queue.join()
        # أوقف العُمال
        for w in workers:
            w.cancel()

    # حفظ النتائج
    with open("documents.json", "w", encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    with open("articles.json", "w", encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    return articles

if __name__ == "__main__":
    seeds = load_urls(URLS_FILE)
    start = time.time()
    arts = asyncio.run(scrape_all(seeds))
    print(f"Scraped {len(arts)} articles in {time.time() - start:.2f} seconds")
