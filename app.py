from flask import Flask, render_template, request, jsonify, send_from_directory
from markupsafe import Markup
import json
import time
import re

app = Flask(__name__)

inverted_index = {}
documents = {}
pagerank_scores = {}
articles = []

def load_data():
    global inverted_index, documents, pagerank_scores, articles

    try:
        with open("inverted_index.json", encoding="utf-8") as f:
            inverted_index = json.load(f)
    except FileNotFoundError:
        inverted_index = {}

    try:
        with open("documents.json", encoding="utf-8") as f:
            documents = json.load(f)
    except FileNotFoundError:
        documents = {}

    try:
        with open("articles.json", encoding="utf-8") as f:
            articles = json.load(f)
    except FileNotFoundError:
        articles = []

    pagerank_scores.clear()
    for url, meta in documents.items():
        pagerank_scores[url] = meta.get("pagerank", 0.0)

load_data()

@app.route('/')
def index():
    return render_template("search.html")

@app.route('/search')
def search():
    try:
        query = request.args.get("q", "").strip().lower()
        use_pr = request.args.get("pagerank", "false") == "true"
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))
        start_time = time.time()

        if query == "thanks big data":
            return jsonify({
                "special_thanks": True,
                "names": [
                    "Dr. Fawzya Ramadan", "Eng. Ahmed Ibrahim", "Eng. Hamada Mostafa",
                    "Eng. Ahmed Abdeltawwab", "Eng. Alaa Nabil"
                ],
                "message": "We sincerely thank our professors and teaching assistants for their guidance and support throughout this Big Data project.",
                "time": time.time() - start_time
            })

        is_phrase = '"' in query
        if is_phrase:
            phrase = re.findall(r'"([^"]*)"', query)
            terms = re.findall(r'\w+', phrase[0].lower()) if phrase else []
        else:
            terms = re.findall(r'\w+', query)

        if not terms:
            return jsonify({"results": [], "time": 0, "count": 0})

        results = single_term_search(terms[0]) if len(terms) == 1 else multi_term_search(terms)
        
        for r in results:
            snippet = get_snippet(r['url'], terms)
            r['content_snippet'] = Markup(snippet)
            r['matched_terms'] = terms

        ranked = rank_results(results, use_pr)

        total_results = len(ranked)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = ranked[start:end]

        return jsonify({
            "query": query,
            "results": paginated,
            "time": time.time() - start_time,
            "count": total_results,
            "page": page,
            "total_pages": (total_results + page_size - 1) // page_size
        })

    except Exception as e:
        app.logger.error(f"Search error: {e}")
        return jsonify({"error": "Internal server error"}), 500

def single_term_search(term):
    return [
        {"url": url, "title": documents.get(url, {}).get("title", url), "score": count}
        for url, count in inverted_index.get(term, {}).items()
    ]

def multi_term_search(terms):
    scores = {}
    for term in terms:
        for url, cnt in inverted_index.get(term, {}).items():
            scores[url] = scores.get(url, 0) + cnt
    return [{"url": url, "title": documents.get(url, {}).get("title", url), "score": sc} for url, sc in scores.items()]

def get_snippet(url, terms):
    for art in articles:
        if art.get("url") == url:
            content = re.sub(r'&\w+;', '', art.get("content", ""))
            content = re.sub(r'\s+', ' ', content)
            snippet = ""
            for term in terms:
                match = re.search(r'(.{0,30}\b' + re.escape(term) + r'\b.{0,30})', content, re.IGNORECASE)
                if match:
                    snippet = f"...{match.group(1).strip()}..."
                    break
            if not snippet:
                snippet = (content[:150] + "...") if len(content) > 150 else content
            for term in terms:
                snippet = re.sub(fr'(\b{re.escape(term)}\b)', r'<mark>\1</mark>', snippet, flags=re.IGNORECASE)
            return snippet
    return ""

def rank_results(results, use_pagerank):
    ranked = []
    for r in results:
        url = r["url"]
        title = r["title"].lower()
        pagerank_score = pagerank_scores.get(url, 0)

        content = ""
        for art in articles:
            if art.get("url") == url:
                content = art.get("content", "").lower()
                break

        terms = r.get("matched_terms", [])
        term_counts = {term: title.count(term) + content.count(term) for term in terms}
        total_counts = sum(term_counts.values())
        score = r.get("score", 0) + total_counts + (pagerank_score * 10 if use_pagerank else 0)

        ranked.append({
            "url": url, "title": r["title"], "content_snippet": r.get("content_snippet", ""),
            "pagerank_score": pagerank_score, "score": score, "term_counts": term_counts,
            "total_term_count": total_counts
        })
    return sorted(ranked, key=lambda x: x["total_term_count"], reverse=True)

if __name__ == "__main__":
    app.run(debug=True)
