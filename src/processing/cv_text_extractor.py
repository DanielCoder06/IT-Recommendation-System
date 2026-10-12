
from pathlib import Path

import pymupdf


def _extract_blocks(page) -> list[dict]:
    """Trích xuất các block văn bản không rỗng cùng tọa độ."""
    blocks = []

    for block in page.get_text("blocks"):
        x0, y0, x1, y1, text = block[:5]

        if not text or not text.strip():
            continue

        blocks.append(
            {
                "x0": float(x0),
                "y0": float(y0),
                "x1": float(x1),
                "y1": float(y1),
                "text": text.strip(),
            }
        )

    return blocks



def _find_column_boundary(
    blocks: list[dict],
    page_width: float,
) -> float | None:
    """Tìm ranh giới hai cột bằng khoảng trống giữa các block."""
    if len(blocks) < 8:
        return None

    # Bỏ qua block quá rộng, thường là header hoặc width content
    candidates = [
        block
        for block in blocks
        if block["x1"] - block["x0"] < page_width * 0.75 
    ]

    if len(candidates) < 8:
        return None

    # Chỉ dùng nội dung phần thân CV
    body_candidates = [
        block for block in candidates if block["y0"] >= 75
    ]

    if len(body_candidates) < 8:
        return None

    # Sắp xếp các khoảng X theo tọa độ bắt đầu.
    intervals = sorted(
        (block["x0"], block["x1"])
        for block in body_candidates
    )

    # Gộp các khoảng X chồng lấn nhau.
    merged = []

    for x0, x1 in intervals:
        if not merged or x0 > merged[-1][1]:
            merged.append([x0, x1])
        else:
            merged[-1][1] = max(merged[-1][1], x1)

    # Tìm khoảng trống đủ rộng ở vùng giữa trang.
    search_min = page_width * 0.25
    search_max = page_width * 0.75
    valid_gaps = []

    for i in range(len(merged) - 1):
        gap_start = merged[i][1]
        gap_end = merged[i + 1][0]
        gap_width = gap_end - gap_start

        if (
            gap_width < page_width * 0.03
            or gap_start < search_min
            or gap_end > search_max
        ):
            continue

        boundary = (gap_start + gap_end) / 2

        left_count = sum(
            block["x1"] <= boundary
            for block in body_candidates
        )
        right_count = sum(
            block["x0"] >= boundary
            for block in body_candidates
        )

        print(
            f"[DEBUG] Gap=({gap_start:.2f}, {gap_end:.2f}), "
            f"width={gap_width:.2f}, boundary={boundary:.2f}, "
            f"left={left_count}, right={right_count}"
        )

        if left_count >= 4 and right_count >= 4:
            valid_gaps.append(
                (gap_width, boundary, left_count, right_count)
            )

    print(f"[DEBUG] Valid gaps: {valid_gaps}")

    if not valid_gaps:
        return None

    _, boundary, _, _ = max(
        valid_gaps,
        key=lambda item: (
            item[0] * min(item[2], item[3]),
            min(item[2], item[3]),
        ),
    )

    print(f"[DEBUG] Selected column boundary: {boundary:.2f}")
    return boundary

def _order_blocks(
    blocks: list[dict],
    page_width: float,
) -> list[dict]:
    """Sắp xếp CV một cột, hai cột hoặc header trên hai cột."""

    if len(blocks) < 8:
        return sorted(blocks, key=lambda b: (b["y0"], b["x0"]))

    boundary = _find_column_boundary(blocks, page_width)

    if boundary is None:
        return sorted(blocks, key=lambda b: (b["y0"], b["x0"]))

    # Xác định vị trí bắt đầu phần thân.
    body_start = min(
        block["y0"]
        for block in blocks
        if block["x1"] - block["x0"] < page_width * 0.75
        and block["y0"] >= 75
    )

    header_blocks = [
        block for block in blocks
        if block["y1"] <= body_start
    ]

    body_blocks = [
        block for block in blocks
        if block["y1"] > body_start
    ]

    left_blocks = []
    right_blocks = []
    spanning_blocks = []

    for block in body_blocks:
        x0 = block["x0"]
        x1 = block["x1"]

        if x1 <= boundary:
            left_blocks.append(block)
        elif x0 >= boundary:
            right_blocks.append(block)
        else:
            spanning_blocks.append(block)

    header_blocks.sort(key=lambda b: (b["y0"], b["x0"]))
    left_blocks.sort(key=lambda b: (b["y0"], b["x0"]))
    right_blocks.sort(key=lambda b: (b["y0"], b["x0"]))
    spanning_blocks.sort(key=lambda b: (b["y0"], b["x0"]))

    print(
        f"[DEBUG] Header={len(header_blocks)}, "
        f"left={len(left_blocks)}, "
        f"right={len(right_blocks)}, "
        f"spanning={len(spanning_blocks)}"
    )

    # Header trước, sau đó đọc cột trái và cột phải.
    return (
        header_blocks
        + left_blocks
        + spanning_blocks
        + right_blocks
    )


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Trích xuất văn bản PDF và khôi phục thứ tự đọc cơ bản."""
    pdf_path = Path(pdf_path)
    pages_text = []

    with pymupdf.open(pdf_path) as document:
        for page in document:
            blocks = _extract_blocks(page)
            ordered_blocks = _order_blocks(blocks, page.rect.width)

            page_text = "\n".join(
                block["text"] for block in ordered_blocks
            )
            pages_text.append(page_text)

    return "\n\n".join(pages_text)
