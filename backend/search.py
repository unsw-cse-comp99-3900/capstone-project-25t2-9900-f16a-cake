import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

ALL_KEYWORDS = [
    "machine learning", "image recognition", "deep learning", "computer vision", "neural network",
    "natural language processing", "NLP", "text analysis", "language model", "BERT",
    "big data", "data analysis", "business intelligence", "decision support", "data mining"
]

DATABASE = [
    {
        "id": 1,
        "title": "Applications of Machine Learning in Image Recognition",
        "keywords": ["machine learning", "image recognition", "deep learning", "computer vision", "neural network"],
        "keywords_encoded": [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "url": "https://example.com/ml-image-recognition",
        "year": "2023"
    },
    {
        "id": 2,
        "title": "Current Developments in Natural Language Processing",
        "keywords": ["natural language processing", "NLP", "text analysis", "language model", "BERT"],
        "keywords_encoded": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
        "url": "https://example.com/nlp-development",
        "year": "2022"
    },
    {
        "id": 3,
        "title": "Applications of Big Data Analysis in Business Decision Making",
        "keywords": ["big data", "data analysis", "business intelligence", "decision support", "data mining"],
        "keywords_encoded": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
        "url": "https://example.com/big-data-business",
        "year": "2023"
    },
    {
        "id": 4,
        "title": "Advancements in Deep Learning for Image Recognition and Computer Vision",
        "keywords": ["deep learning", "image recognition", "computer vision"],
        "keywords_encoded": [0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "url": "https://example.com/deep-learning-vision",
        "year": "2021"
    },
    {
        "id": 5,
        "title": "The Role of Big Data and Data Analysis in Business Intelligence",
        "keywords": ["big data", "data analysis", "business intelligence"],
        "keywords_encoded": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0],
        "url": "https://example.com/big-data-bi",
        "year": "2024"
    },
    {
        "id": 6,
        "title": "Integration of Machine Learning and Neural Networks in Computer Vision",
        "keywords": ["machine learning", "neural network", "computer vision"],
        "keywords_encoded": [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "url": "https://example.com/ml-nn-vision",
        "year": "2025"
    },
    {
        "id": 7,
        "title": "Applications of NLP and Language Models in Text Analysis",
        "keywords": ["natural language processing", "language model", "text analysis"],
        "keywords_encoded": [0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0],
        "url": "https://example.com/nlp-text-analysis",
        "year": "2025"
    },
    {
        "id": 8,
        "title": "Practical Deep Learning and Neural Network Methods for Image Recognition",
        "keywords": ["deep learning", "neural network", "image recognition"],
        "keywords_encoded": [0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "url": "https://example.com/dl-nn-image",
        "year": "2025"
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
