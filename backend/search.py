import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import database

# 从数据库获取关键词列表
def get_all_keywords():
    """从数据库获取所有关键词"""
    keywords, error = database.get_all_keywords_from_db()
    if error:
        return []
    return keywords

def extract_keywords(text):
    keywords = []
    text_lower = text.lower()
    all_keywords = get_all_keywords()
    
    # 首先尝试匹配数据库中的关键词
    for keyword in all_keywords:
        if keyword.lower() in text_lower:
            keywords.append(keyword)
    
    # 如果没有找到匹配的关键词，尝试部分匹配
    if not keywords:
        words = re.findall(r'\b\w+\b', text.lower())
        for word in words:
            for keyword in all_keywords:
                if word in keyword.lower() or keyword.lower() in word:
                    if keyword not in keywords:
                        keywords.append(keyword)
        
        # 如果仍然没有匹配，返回输入的词汇但限制数量
        if not keywords:
            keywords = words[:3]  # 减少到3个词以提高精确度
    
    return keywords

def multi_hot_encode(keywords):
    all_keywords = get_all_keywords()
    encoded = [0] * len(all_keywords)
    for keyword in keywords:
        if keyword in all_keywords:
            idx = all_keywords.index(keyword)
            encoded[idx] = 1
    return encoded

def normalize_encoded_vector(encoded_vector, target_length):
    """将编码向量标准化到目标长度"""
    if len(encoded_vector) == target_length:
        return encoded_vector
    elif len(encoded_vector) > target_length:
        return encoded_vector[:target_length]
    else:
        return encoded_vector + [0] * (target_length - len(encoded_vector))

def jaccard_similarity(set1, set2):
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union else 0

def calculate_similarity(query_encoded, db_encoded, query_text, db_title):
    # 确保两个编码向量长度一致
    max_length = max(len(query_encoded), len(db_encoded))
    query_encoded = normalize_encoded_vector(query_encoded, max_length)
    db_encoded = normalize_encoded_vector(db_encoded, max_length)
    
    # Keyword similarity
    q_set = {i for i, v in enumerate(query_encoded) if v}
    d_set = {i for i, v in enumerate(db_encoded) if v}
    
    # 如果没有公共关键词，直接返回0
    if not (q_set & d_set):
        # 检查标题是否有匹配词汇
        q_words = set(re.findall(r'\b\w+\b', query_text.lower()))
        d_words = set(re.findall(r'\b\w+\b', db_title.lower()))
        common_words = q_words & d_words
        
        # 如果标题也没有匹配词汇，返回0
        if not common_words:
            return 0.0
    
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
    
    # 确保最小阈值
    return final_score if final_score > 0.05 else 0.0
