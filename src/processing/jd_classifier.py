import numpy as np
from enum import Enum
import re

class JDCategory(Enum):
    REQUIREMENT = "REQUIREMENT"
    RESPONSIBILITY = "RESPONSIBILITY"
    BENEFIT = "BENEFIT"
    COMPANY = "COMPANY"
    ANTI_REQ = "ANTI_REQ"
    GENERAL = "GENERAL"

# BỘ LỌC TỪ KHÓA NHANH 
EXACT_KEYWORDS = {
    JDCategory.REQUIREMENT: [
        "about you", "your profile", "requirement", "requirements", 
        "qualification", "qualifications", "what you bring", "what you'll bring", "what you will bring", 
        "who you are", "what we are looking for", "we are looking for", 
        "great fit", "a plus", "nice to have", "bonus", "essential", 
        "desirable experience", "must-haves", "skills and experience", 
        "desired skills", "your skills", "profile"
    ],
    JDCategory.RESPONSIBILITY: [
        "your job", "your role", "responsibility", "responsibilities", 
        "what you will do", "what you'll do", "your mission", 
        "the technical challenge", "tasks", "position summary", 
        "what you will be doing", "your tasks", "description", "duties",
        "the role", "about the role"
    ],
    JDCategory.BENEFIT: [
        "benefit", "benefits", "perks", "what we offer", "why us", 
        "your benefits", "what we can offer you", "total rewards", 
        "why collaborate", "what's in it for you"
    ],
    JDCategory.COMPANY: [
        "about our company", "about us", "who we are", "the team", 
        "about the opportunity", "our community", "about quotient"
    ],
    JDCategory.ANTI_REQ: [
        "not looking for", "don't apply if"
    ]
}

# MỎ NEO NGỮ NGHĨA CHO AI
ANCHOR_TEXTS = {
    JDCategory.REQUIREMENT: "Qualifications, core skills, experience required, candidate requirements, ideal candidate, technical skills",
    JDCategory.RESPONSIBILITY: "Day to day responsibilities, daily tasks, accountability, in this role you will",
    JDCategory.BENEFIT: "Compensation, health insurance, flexible working, company culture, salary",
    JDCategory.COMPANY: "Company vision, our story, mission statement",
    JDCategory.ANTI_REQ: "What we are not looking for, you are not a good fit"
}

_anchor_embeddings = None

def _get_anchor_embeddings():
    global _anchor_embeddings
    if _anchor_embeddings is None:
        from src.models.embedding_model import model
        _anchor_embeddings = {
            category: model.encode(text, normalize_embeddings=True)
            for category, text in ANCHOR_TEXTS.items()
        }
    return _anchor_embeddings
# Hàm phân loại tiêu đề JD dựa trên từ khóa và embedding
def classify_heading(heading_text: str, threshold: float = 0.45) -> JDCategory:
    if not heading_text or not heading_text.strip():
        return JDCategory.GENERAL

    text_lower = heading_text.lower()

    # Quét từ khóa nhanh
    for category, keywords in EXACT_KEYWORDS.items():
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                return category

    # Fallback sang AI Embedding
    from src.models.embedding_model import model
    anchors = _get_anchor_embeddings()
    heading_emb = model.encode(heading_text, normalize_embeddings=True)

    best_category = JDCategory.GENERAL
    max_similarity = 0.0

    for category, anchor_emb in anchors.items():
        similarity = float(np.dot(heading_emb, anchor_emb))
        if similarity > max_similarity and similarity >= threshold:
            max_similarity = similarity
            best_category = category

    return best_category