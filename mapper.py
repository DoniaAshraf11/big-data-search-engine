import re

def mapper(articles):
    mapped = []
    for article in articles:
        url = article["url"]
        words = article["content"].split()
        for word in words:
            cleaned = re.sub(r'\W+', '', word).lower()
            if cleaned:
                mapped.append((cleaned, url))
    return mapped
