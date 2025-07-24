import re
import uuid
import datetime
import logging
import pdfplumber
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json

# Silence pdfminer/pdfplumber font warnings
logging.getLogger("pdfminer").setLevel(logging.ERROR)


def extract_text_from_pdf(path):
    """
    提取 PDF 中文本，并返回整个文档的字符串。
    """
    texts = []
    with pdfplumber.open(path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            try:
                text = page.extract_text()
            except Exception as e:
                logging.error(f"第{page_num}页提取文本时出错: {e}")
                continue
            if text:
                texts.append(text)
    return "\n".join(texts)


def parse_qa_pairs(full_text):
    """
    从全文中提取问答对。
    匹配问号结尾或数字标题行作为问题，后续内容作为答案。
    """
    docs = []
    lines = [line.strip() for line in full_text.splitlines()]
    heading_re = re.compile(r'^(\d+(?:\.\d+)*):\s*(.+)')
    i = 0
    while i < len(lines):
        question = None
        line = lines[i]
        if line.endswith('?') or line.endswith('？'):
            question = line
        else:
            m = heading_re.match(line)
            if m:
                question = m.group(2)
        if question:
            answer_lines = []
            j = i + 1
            while j < len(lines) and lines[j]:
                if lines[j].endswith('?') or heading_re.match(lines[j]):
                    break
                answer_lines.append(lines[j])
                j += 1
            answer = ' '.join(answer_lines).strip()
            docs.append({
                'id': f"qa_{uuid.uuid4().hex[:8]}",
                'question': question,
                'answer': answer
            })
            i = j
        else:
            i += 1
    return docs


def build_docs_from_pdf(pdf_path, title, url=None, last_edited=None):
    """
    从 PDF 构建问答文档列表。
    """
    text = extract_text_from_pdf(pdf_path)
    qa = parse_qa_pairs(text)
    docs = []
    for item in qa:
        docs.append({
            **item,
            'source': {
                'title': title,
                'url': url or pdf_path,
                'last_edited': last_edited or datetime.date.today().isoformat()
            }
        })
    return docs


def build_docs_from_web(url, title=None, last_edited=None):
    """
    从网页 URL 构建问答文档列表。

    遍历所有标题标签（h1-h6），
    提取以问号结尾的标题为问题，
    收集其后连续内容作为答案，直到下一个标题。
    """
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    docs = []
    for header in soup.find_all(['h1','h2','h3','h4','h5','h6']):
        question = header.get_text(strip=True)
        if question.endswith('?'):
            answer_parts = []
            for sib in header.next_siblings:
                if getattr(sib, 'name', None) and sib.name.startswith('h') and sib.name[1].isdigit():
                    break
                if hasattr(sib, 'get_text'):
                    text = sib.get_text(strip=True)
                    if text:
                        answer_parts.append(text)
            answer = ' '.join(answer_parts)
            docs.append({
                'id': f"qa_{uuid.uuid4().hex[:8]}",
                'question': question,
                'answer': answer,
                'source': {
                    'title': title or url,
                    'url': url,
                    'last_edited': last_edited or datetime.date.today().isoformat()
                }
            })
    return docs


if __name__ == '__main__':
    # 1. 初始静态文档（示例）
    docs = [
      {
        'id': 'zid_001',
        'question': 'What is a zID?',
        'answer': "Your zID is your username for virtually all systems run by UNSW and CSE. It consists of a 'z', followed by your student or staff number (e.g. z1234567).",
        'source': {'title': 'Getting a zID', 'url': 'https://taggi.cse.unsw.edu.au/FAQ/Getting_a_zID/', 'last_edited': '09/11/2020'}
      },
      # ... 其他静态条目省略
    ]

    # 2. 从 PDF 解析并加入
    pdf_path = r"Accessing Your Files - CSE taggi.pdf"
    pdf_docs = build_docs_from_pdf(pdf_path, title='Sample PDF', url=None, last_edited='2025-07-15')
    docs.extend(pdf_docs)

    # 3. 从网页解析并加入
    web_url = 'https://taggi.cse.unsw.edu.au/FAQ/Getting_a_zID/'
    web_docs = build_docs_from_web(web_url, title='Getting a zID', last_edited='09/11/2020')
    docs.extend(web_docs)

    # 4. 嵌入与索引
    model = SentenceTransformer('all-MiniLM-L6-v2')
    texts = [d['question'] + ' ' + d['answer'] for d in docs]
    embeddings = model.encode(texts, show_progress_bar=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings, dtype='float32'))

    # 打印索引信息
    print(f"Indexed {index.ntotal} vectors.")
    print(index)

    faiss.write_index(index, 'zid_faq.index')
    print("FAISS index saved to 'zid_faq.index'.")

    # 6. 保存文档到 JSON
    with open('zid_faq_docs.json', 'w', encoding='utf-8') as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)
    print("Saved docs to 'zid_faq_docs.json'.")
