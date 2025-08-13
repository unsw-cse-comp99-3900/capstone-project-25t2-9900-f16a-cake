"""
Search Module for Cake Recipe Recommendation System

This module provides search and similarity calculation functionality for the cake recipe
recommendation system. It implements keyword extraction, multi-hot encoding, and
various similarity metrics to find the most relevant recipes based on user queries.

Key Features:
- Keyword extraction from text using database keywords
- Multi-hot encoding for keyword representation
- Jaccard and cosine similarity calculations
- Combined similarity scoring with keyword and title matching
- Vector normalization for consistent comparison

Author: Capstone Project Team
Date: 2024
Version: 1.0
"""

import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import database

def get_all_keywords():
    """
    Retrieve all keywords from the database
    
    Returns:
        list: List of all available keywords from the database
    """
    keywords, error = database.get_all_keywords_from_db()
    if error:
        return []
    return keywords

def extract_keywords(text):
    """
    Extract relevant keywords from input text using database keywords
    
    Args:
        text (str): Input text to extract keywords from
        
    Returns:
        list: List of extracted keywords
    """
    keywords = []
    text_lower = text.lower()
    all_keywords = get_all_keywords()
    
    # First try to match exact keywords from database
    for keyword in all_keywords:
        if keyword.lower() in text_lower:
            keywords.append(keyword)
    
    # If no exact matches found, try partial matching
    if not keywords:
        words = re.findall(r'\b\w+\b', text.lower())
        for word in words:
            for keyword in all_keywords:
                if word in keyword.lower() or keyword.lower() in word:
                    if keyword not in keywords:
                        keywords.append(keyword)
        
        # If still no matches, return input words but limit quantity
        if not keywords:
            keywords = words[:3]  # Reduce to 3 words for better precision
    
    return keywords

def multi_hot_encode(keywords):
    """
    Convert keywords list to multi-hot encoded vector
    
    Args:
        keywords (list): List of keywords to encode
        
    Returns:
        list: Binary encoded vector where 1 indicates presence of keyword
    """
    all_keywords = get_all_keywords()
    encoded = [0] * len(all_keywords)
    for keyword in keywords:
        if keyword in all_keywords:
            idx = all_keywords.index(keyword)
            encoded[idx] = 1
    return encoded

def normalize_encoded_vector(encoded_vector, target_length):
    """
    Normalize encoded vector to target length
    
    Args:
        encoded_vector (list): Input encoded vector
        target_length (int): Desired length of output vector
        
    Returns:
        list: Normalized vector with target length
    """
    if len(encoded_vector) == target_length:
        return encoded_vector
    elif len(encoded_vector) > target_length:
        return encoded_vector[:target_length]
    else:
        return encoded_vector + [0] * (target_length - len(encoded_vector))

def jaccard_similarity(set1, set2):
    """
    Calculate Jaccard similarity between two sets
    
    Args:
        set1 (set): First set
        set2 (set): Second set
        
    Returns:
        float: Jaccard similarity score between 0 and 1
    """
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union else 0

def calculate_similarity(query_encoded, db_encoded, query_text, db_title):
    """
    Calculate comprehensive similarity score between query and database entry
    
    This function combines keyword similarity (using Jaccard and cosine) with
    title similarity to provide a robust similarity measure.
    
    Args:
        query_encoded (list): Encoded vector of query keywords
        db_encoded (list): Encoded vector of database entry keywords
        query_text (str): Original query text
        db_title (str): Database entry title
        
    Returns:
        float: Combined similarity score between 0 and 1
    """
    # Ensure both encoded vectors have consistent length
    max_length = max(len(query_encoded), len(db_encoded))
    query_encoded = normalize_encoded_vector(query_encoded, max_length)
    db_encoded = normalize_encoded_vector(db_encoded, max_length)
    
    # Keyword similarity calculation
    q_set = {i for i, v in enumerate(query_encoded) if v}
    d_set = {i for i, v in enumerate(db_encoded) if v}
    
    # If no common keywords, return 0 directly
    if not (q_set & d_set):
        # Check if title has matching words
        q_words = set(re.findall(r'\b\w+\b', query_text.lower()))
        d_words = set(re.findall(r'\b\w+\b', db_title.lower()))
        common_words = q_words & d_words
        
        # If title also has no matching words, return 0
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
    
    # Ensure minimum threshold
    return final_score if final_score > 0.05 else 0.0
