import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

ALL_KEYWORDS = [
    "home", "directory", "homedir", "files", "fileserver", "sftp", "upload", "download", 
    "account", "group", "class", "expiring", "expiry", "disabled", "permitted"
]

DATABASE = [
    {
        "id": 1,
        "title": "Accessing Your Files",
        "keywords": ["home", "directory", "homedir", "files", "fileserver", "sftp", "upload", "download"],
        "keywords_encoded": [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
        "pdf_path": "Accessing Your Files - CSE taggi.pdf",
        "year": "2023"
    },
    {
        "id": 2,
        "title": "Account Classes and Groups",
        "keywords": ["account", "group", "class", "expiring", "expiry"],
        "keywords_encoded": [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0],
        "pdf_path": "Account Classes and Groups - CSE taggi.pdf",
        "year": "2022"
    },
    {
        "id": 3,
        "title": "Account Disabled",
        "keywords": ["account", "disabled", "permitted"],
        "keywords_encoded": [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1],
        "pdf_path": "Account Disabled - CSE taggi.pdf",
        "year": "2023"
    }
]



def extract_keywords(text):
    keywords = []
    text_lower = text.lower()
    for keyword in ALL_KEYWORDS:
        if keyword.lower() in text_lower:
            keywords.append(keyword)
    if not keywords:
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = words[:5]
    return keywords

def multi_hot_encode(keywords):
    encoded = [0] * len(ALL_KEYWORDS)
    for keyword in keywords:
        if keyword in ALL_KEYWORDS:
            idx = ALL_KEYWORDS.index(keyword)
            encoded[idx] = 1
    return encoded

def jaccard_similarity(set1, set2):
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union else 0

def calculate_similarity(query_encoded, db_encoded, query_text, db_title):
    # Keyword similarity
    q_set = {i for i, v in enumerate(query_encoded) if v}
    d_set = {i for i, v in enumerate(db_encoded) if v}
    jaccard = jaccard_similarity(q_set, d_set)
    cosine = cosine_similarity([query_encoded], [db_encoded])[0][0] if any(query_encoded) and any(db_encoded) else 0
    keyword_sim = 0.7 * jaccard + 0.3 * cosine

    # Title similarity (word-level matching)
    q_words = set(re.findall(r'\b\w+\b', query_text.lower()))
    d_words = set(re.findall(r'\b\w+\b', db_title.lower()))
    common_words = q_words & d_words
    title_sim = len(common_words) / len(q_words) if len(q_words) else 0

    # Combined score with higher keyword weight
    final_score = 0.75 * keyword_sim + 0.25 * title_sim
    return final_score
