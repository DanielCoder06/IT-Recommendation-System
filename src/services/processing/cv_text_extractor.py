from pathlib import Path
import pymupdf

def _extract_blocks(page) -> list[dict]:
    """Trích xuất các block văn bản không rỗng cùng tọa độ."""
    blocks = []
    for block in page.get_text("blocks"):
        x0, y0, x1, y1, text = block[:5]
        if not text or not text.strip():
            continue
        blocks.append({
            "x0": float(x0), "y0": float(y0),
            "x1": float(x1), "y1": float(y1),
            "text": text.strip(),
        })
    return blocks

def _find_column_boundary(blocks: list[dict], page_width: float) -> float | None:
    """Tìm ranh giới hai cột bằng khoảng trống giữa các block."""
    if len(blocks) < 8:
        return None

    candidates = [b for b in blocks if b["x1"] - b["x0"] < page_width * 0.75]
    body_candidates = [b for b in candidates if b["y0"] >= 75]

    if len(body_candidates) < 8:
        return None

    intervals = sorted((b["x0"], b["x1"]) for b in body_candidates)
    merged = []
    for x0, x1 in intervals:
        if not merged or x0 > merged[-1][1]:
            merged.append([x0, x1])
        else:
            merged[-1][1] = max(merged[-1][1], x1)

    search_min, search_max = page_width * 0.25, page_width * 0.75
    valid_gaps = []
    for i in range(len(merged) - 1):
        gap_start, gap_end = merged[i][1], merged[i + 1][0]
        gap_width = gap_end - gap_start
        if gap_width < page_width * 0.03 or gap_start < search_min or gap_end > search_max:
            continue

        boundary = (gap_start + gap_end) / 2
        left_count = sum(b["x1"] <= boundary for b in body_candidates)
        right_count = sum(b["x0"] >= boundary for b in body_candidates)
        
        if left_count >= 4 and right_count >= 4:
            valid_gaps.append((gap_width, boundary, left_count, right_count))

    if not valid_gaps:
        return None

    _, boundary, _, _ = max(valid_gaps, key=lambda item: (item[0] * min(item[2], item[3]), min(item[2], item[3])))
    return boundary

def _order_blocks(blocks: list[dict], page_width: float) -> list[dict]:
    """Sắp xếp CV một cột, hai cột hoặc header trên hai cột."""
    if len(blocks) < 8:
        return sorted(blocks, key=lambda b: (b["y0"], b["x0"]))

    boundary = _find_column_boundary(blocks, page_width)
    if boundary is None:
        return sorted(blocks, key=lambda b: (b["y0"], b["x0"]))

    body_start = min(b["y0"] for b in blocks if b["x1"] - b["x0"] < page_width * 0.75 and b["y0"] >= 75)
    header_blocks = [b for b in blocks if b["y1"] <= body_start]
    body_blocks = [b for b in blocks if b["y1"] > body_start]

    left_blocks, right_blocks, spanning_blocks = [], [], []
    for block in body_blocks:
        if block["x1"] <= boundary:
            left_blocks.append(block)
        elif block["x0"] >= boundary:
            right_blocks.append(block)
        else:
            spanning_blocks.append(block)

    header_blocks.sort(key=lambda b: (b["y0"], b["x0"]))
    left_blocks.sort(key=lambda b: (b["y0"], b["x0"]))
    right_blocks.sort(key=lambda b: (b["y0"], b["x0"]))
    spanning_blocks.sort(key=lambda b: (b["y0"], b["x0"]))

    return header_blocks + left_blocks + spanning_blocks + right_blocks

def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Trích xuất văn bản PDF và khôi phục thứ tự đọc cơ bản."""
    pdf_path = Path(pdf_path)
    pages_text = []
    with pymupdf.open(pdf_path) as document:
        for page in document:
            blocks = _extract_blocks(page)
            ordered_blocks = _order_blocks(blocks, page.rect.width)
            page_text = "\n".join(block["text"] for block in ordered_blocks)
            pages_text.append(page_text)
    return "\n\n".join(pages_text)