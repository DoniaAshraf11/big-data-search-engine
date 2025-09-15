from collections import defaultdict

def reducer(combined_data):
    inverted_index = defaultdict(dict)
    for word, url_counts in combined_data.items():
        for url, count in url_counts.items():
            inverted_index[word][url] = count
    return inverted_index
