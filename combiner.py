from collections import defaultdict

def combiner(mapped_data):
    combined = defaultdict(lambda: defaultdict(int))
    for word, url in mapped_data:
        combined[word][url] += 1
    return combined
