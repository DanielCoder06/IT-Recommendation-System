
from pathlib import Path

import pymupdf


def _extract_blocks(page) -> list[dict]:
    """Extract non-empty text blocks and their coordinates."""
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
    """Tìm khoảng trống ngang thực sự giữa hai vùng nội dung."""
    if len(blocks) < 8:
        return None

    # Các block trải gần toàn chiều ngang thường là tiêu đề hoặc nội dung
    # một cột, nên không dùng chúng để xác định hai cột.
    candidates = [
        block for block in blocks
        if block["x1"] - block["x0"] < page_width * 0.75
    ]

    if len(candidates) < 8:
        return None

    # Xét các vị trí x mà block kết thúc và block khác bắt đầu.
    intervals = sorted(
        (block["x0"], block["x1"])
        for block in candidates
    )

    # Gộp các vùng ngang đang chồng lấn hoặc gần nhau.
    merged = []
    for x0, x1 in intervals:
        if not merged or x0 > merged[-1][1]:
            merged.append([x0, x1])
        else:
            merged[-1][1] = max(merged[-1][1], x1)

    # Tìm khoảng trống đủ rộng để có thể là rãnh giữa hai cột.
    gaps = []
    for i in range(len(merged) - 1):
        gap_start = merged[i][1]
        gap_end = merged[i + 1][0]
        gap_width = gap_end - gap_start

        if gap_width < page_width * 0.05:
            continue

        boundary = (gap_start + gap_end) / 2

        left_count = sum(
            block["x1"] <= boundary for block in candidates
        )
        right_count = sum(
            block["x0"] >= boundary for block in candidates
        )

        if left_count >= 4 and right_count >= 4:
            gaps.append(
                (gap_width, boundary, left_count, right_count)
            )

    if not gaps:
        return None

    # Ưu tiên rãnh rộng và có đủ nội dung ở cả hai bên.
    _, boundary, _, _ = max(
        gaps,
        key=lambda item: (
            item[0] * min(item[2], item[3]),
            min(item[2], item[3]),
        ),
    )

    return boundary

def _order_blocks(
    blocks: list[dict],
    page_width: float,
) -> list[dict]:
    """Sắp xếp block theo cột khi có bằng chứng rõ ràng về hai cột."""
    boundary = _find_column_boundary(blocks, page_width)

    if boundary is None:
        # Không đủ bằng chứng có hai cột: giữ thứ tự đọc gần theo hàng.
        return sorted(
            blocks,
            key=lambda block: (block["y0"], block["x0"]),
        )

    left_blocks = [
        block for block in blocks
        if block["x1"] <= boundary
    ]
    right_blocks = [
        block for block in blocks
        if block["x0"] >= boundary
    ]

    # Block giao qua ranh giới được xử lý riêng, không tự ý loại bỏ.
    middle_blocks = [
        block for block in blocks
        if block not in left_blocks and block not in right_blocks
    ]

    left_blocks.sort(key=lambda block: (block["y0"], block["x0"]))
    right_blocks.sort(key=lambda block: (block["y0"], block["x0"]))
    middle_blocks.sort(key=lambda block: (block["y0"], block["x0"]))

    return left_blocks + middle_blocks + right_blocks

def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Extract PDF text and restore a basic column reading order."""
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