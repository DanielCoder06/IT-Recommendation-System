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

# BỘ LỌC TỪ KHÓA NHANH (Eng)
EXACT_KEYWORDS = {
    JDCategory.REQUIREMENT: [
        "about you", "your profile", "requirement", "requirements", 
        "qualification", "qualifications", "what you bring", "what you'll bring", "what you will bring", 
        "who you are", "what we are looking for", "we are looking for", "who we're looking for",
        "great fit", "a plus", "nice to have", "bonus", "essential", 
        "desirable experience", "must-haves", "must have", "skills and experience", 
        "desired skills", "your skills", "skills required", "what you need", "what you need to succeed",
        "minimum qualifications", "basic qualifications", "preferred qualifications",
        "candidate profile", "prerequisites", "tech stack", "competencies", "profile"
    ],
    JDCategory.RESPONSIBILITY: [
        "your job", "your role", "responsibility", "responsibilities", "key responsibilities",
        "what you will do", "what you'll do", "what you will be doing", "what you'll be doing",
        "your mission", "the technical challenge", "tasks", "position summary", 
        "your tasks", "description", "duties", "the role", "about the role",
        "scope of work", "role overview", "what to expect", "day-to-day", "daily tasks",
        "how you'll contribute", "how you will contribute", "areas of responsibility"
    ],
    JDCategory.BENEFIT: [
        "benefit", "benefits", "perks", "what we offer", "why us", 
        "your benefits", "what we can offer you", "total rewards", 
        "why collaborate", "what's in it for you", "compensation", "remuneration",
        "our offer", "we offer", "why join us", "why work with us", "employee benefits",
        "what you get", "what you will get", "advantages"
    ],
    JDCategory.COMPANY: [
        "about our company", "about the company", "about us", "who we are", "the team", 
        "about the opportunity", "our community", "company overview", "company profile",
        "our mission", "our story", "working at", "join our team", "meet the team"
    ],
    JDCategory.ANTI_REQ: [
        "not looking for", "don't apply if", "not for you if", "this role is not for you if",
        "who this is not for"
    ]
}

# MÔ TẢ NGỮ NGHĨA CHO CÁC DANH MỤC 
ANCHOR_TEXTS = {
    JDCategory.REQUIREMENT: "Qualifications, core skills, technical requirements, experience required, candidate profile, prerequisites, who you are, what you bring",
    JDCategory.RESPONSIBILITY: "Day to day responsibilities, key duties, daily tasks, accountability, in this role you will, scope of work, what you will do",
    JDCategory.BENEFIT: "Compensation, perks, employee benefits, health insurance, flexible working, salary, why join us, what we offer",
    JDCategory.COMPANY: "Company overview, about us, company culture, who we are, our team, mission statement, our story",
    JDCategory.ANTI_REQ: "What we are not looking for, you are not a good fit, don't apply if, disqualifiers"
}

_anchor_embeddings = None

def _get_anchor_embeddings():
    global _anchor_embeddings
    if _anchor_embeddings is None:
        from src.services.embeddings.embedding_model import model
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

    # Fallback sang AI Embedding (nếu từ khóa không khớp)
    from src.services.embeddings.embedding_model import model
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