import re
from typing import Callable
import numpy as np

# Regex nhận diện gạch đầu dòng (bullet points) tiếng Anh
BULLET_RE = re.compile(r"^\s*([•●▪■◦·‣▸►*]|-|–|\d+[.)])\s+")
# Regex nhận diện phân tách câu tiếng Anh
SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")

def is_bullet(text: str) -> bool:
    return bool(BULLET_RE.match(text))

def strip_bullet(text: str) -> str:
    return BULLET_RE.sub("", text).strip()

def split_text_into_units(text: str) -> list[str]:
    """Tách văn bản tiếng Anh thành các đơn vị ngữ nghĩa (bullet point hoặc câu)."""
    if not text or not text.strip():
        return []

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []

    raw_units: list[str] = []
    for line in lines:
        if is_bullet(line):
            raw_units.append(strip_bullet(line))
        elif raw_units and (line[:1].islower() or (len(raw_units[-1]) >= 60 and raw_units[-1][-1] not in ".;:!?")):
            raw_units[-1] += " " + line
        else:
            raw_units.append(line)

    final_units: list[str] = []
    for unit in raw_units:
        if len(unit.split()) > 35:
            sentences = [s.strip() for s in SENT_SPLIT_RE.split(unit) if s.strip()]
            if sentences:
                final_units.extend(sentences)
            else:
                final_units.append(unit)
        else:
            final_units.append(unit)

    return final_units

class SemanticChunker:
    """
    - Tạo context window trượt để embedding
    - Tính khoảng cách cosine giữa các đơn vị liên tiếp
    - Cắt tại các điểm đổi ngữ nghĩa (vượt ngưỡng phân vị breakpoint_percentile)
    - Đảm bảo giới hạn độ dài hợp lý (min_chars, max_chars)
    """
    def __init__(
        self,
        embed_fn: Callable[[list[str]], np.ndarray] | None = None,
        breakpoint_percentile: float = 70.0,
        min_distance: float = 0.15,
        min_chars: int = 150,
        max_chars: int = 600,
        window: int = 1,
    ):
        if embed_fn is None:
            from src.services.embeddings.embedding_model import model
            self.embed_fn = lambda texts: model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        else:
            self.embed_fn = embed_fn

        self.p = breakpoint_percentile
        self.min_distance = min_distance
        self.min_chars = min_chars
        self.max_chars = max_chars
        self.window = window

    def distances(self, units: list[str]) -> np.ndarray:
        if len(units) < 2:
            return np.empty(0, dtype=float)

        w = self.window
        ctx = [" ".join(units[max(0, i - w) : i + w + 1]) for i in range(len(units))]
        e = np.asarray(self.embed_fn(ctx), dtype=float)
        norm = np.linalg.norm(e, axis=1, keepdims=True) + 1e-9
        e = e / norm
        return 1.0 - np.sum(e[:-1] * e[1:], axis=1)

    def split(self, units: list[str]) -> list[list[str]]:
        if len(units) <= 1:
            return [units] if units else []

        d = self.distances(units)
        if len(d) == 0:
            return [units]

        thr = max(float(np.percentile(d, self.p)), self.min_distance)
        groups: list[list[str]] = []
        cur = [units[0]]

        for i, dist in enumerate(d):
            if dist > thr:
                groups.append(cur)
                cur = []
            cur.append(units[i + 1])
        groups.append(cur)

        return self._enforce_size(groups)

    def _size(self, group: list[str]) -> int:
        return len("\n".join(group))

    def _enforce_size(self, groups: list[list[str]]) -> list[list[str]]:
        merged: list[list[str]] = []
        for g in groups:
            if merged and self._size(g) < self.min_chars and self._size(merged[-1]) + self._size(g) <= self.max_chars:
                merged[-1] = merged[-1] + g
            else:
                merged.append(g)

        if len(merged) > 1 and self._size(merged[0]) < self.min_chars and self._size(merged[0]) + self._size(merged[1]) <= self.max_chars:
            merged[1] = merged[0] + merged[1]
            merged.pop(0)

        out: list[list[str]] = []
        for g in merged:
            cur: list[str] = []
            for u in g:
                if cur and self._size(cur + [u]) > self.max_chars:
                    out.append(cur)
                    cur = []
                cur.append(u)
            if cur:
                out.append(cur)

        return out

    def chunk_text(self, text: str, header: str = "") -> list[str]:
        if not text or not text.strip():
            return []

        if len(text.strip()) <= self.max_chars:
            content = text.strip()
            return [f"[{header}] {content}" if header else content]

        units = split_text_into_units(text)
        if not units:
            return []

        groups = self.split(units)
        result: list[str] = []
        for g in groups:
            body = "\n".join(g).strip()
            if not body:
                continue
            if header:
                result.append(f"[{header}]\n{body}")
            else:
                result.append(body)
        return result