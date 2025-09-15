import networkx as nx
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def calculate_pagerank(articles, damping=0.85, max_iter=100, tol=1e-6):
    G = nx.DiGraph()
    for art in articles:
        G.add_node(art['url'])
    for art in articles:
        src = art['url']
        soup = BeautifulSoup(art['content'], 'html.parser')
        for a in soup.find_all('a', href=True):
            tgt = urljoin(src, a['href'])
            if tgt in G:
                G.add_edge(src, tgt)
    # استخدام النسخة المعتمدة على NumPy فقط
    pr = nx.pagerank(G, alpha=damping, max_iter=max_iter, tol=tol)
    return pr
