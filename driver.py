import json
import asyncio
from scraper import load_urls, scrape_all
from mapper import mapper
from combiner import combiner
from reducer import reducer
from pagerank import calculate_pagerank

def main():
    # 1. Scraping باستخدام البذور من urls.txt
    seeds = load_urls('urls.txt')
    articles = asyncio.run(scrape_all(seeds))

    # 2. Build inverted index
    mapped = mapper(articles)
    combined = combiner(mapped)
    inverted = reducer(combined)
    with open("inverted_index.json", "w", encoding="utf-8") as f:
        json.dump(inverted, f, ensure_ascii=False, indent=2)

    # 3. PageRank
    pr_scores = calculate_pagerank(articles)
    with open("pagerank.json", "w", encoding="utf-8") as f:
        json.dump(pr_scores, f, ensure_ascii=False, indent=2)

    print(f"[✓] Scraped {len(articles)} articles, index & PageRank saved.")

if __name__ == "__main__":
    main()
