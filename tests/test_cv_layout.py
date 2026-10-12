"""
Test kiểm tra tọa độ và thứ tự block được trích xuất từ CV PDF.

Mục tiêu:
1. Mở CV PDF.
2. In bbox (x0, y0, x1, y1), kích thước và nội dung từng block.
3. Báo cáo bbox bất thường hoặc nằm ngoài trang để dễ đối chiếu trực quan.

Lưu ý:
- Test này kiểm tra tọa độ/trích xuất block, không đánh giá ngữ nghĩa section.
- Gốc tọa độ PyMuPDF nằm ở góc trên bên trái; đơn vị là point.
- Không dùng một tọa độ X cố định để kết luận CV có một hay hai cột.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pymupdf

from src.processing.cv_text_extractor import _extract_blocks


DEFAULT_PDF = Path("data/VCTD.pdf")


def inspect_pdf(pdf_path: Path, page_number: int | None = None) -> int:
    """In tọa độ và nội dung block trên một hoặc tất cả các trang."""
    if not pdf_path.is_file():
        print(f"[ERROR] Không tìm thấy PDF: {pdf_path}")
        return 2

    try:
        document = pymupdf.open(pdf_path)
    except Exception as exc:
        print(f"[ERROR] Không mở được PDF: {exc}")
        return 2

    try:
        if document.page_count == 0:
            print("[ERROR] PDF không có trang.")
            return 2

        if page_number is not None and not 1 <= page_number <= document.page_count:
            print(f"[ERROR] Trang {page_number} không hợp lệ; PDF có {document.page_count} trang.")
            return 2

        page_indices = (
            [page_number - 1]
            if page_number is not None
            else list(range(document.page_count))
        )

        total_blocks = 0
        invalid_boxes = 0
        outside_boxes = 0

        print("=" * 100)
        print("CV PDF — BLOCK COORDINATE TEST")
        print("=" * 100)
        print(f"PDF: {pdf_path}")
        print("BBox = (x0, y0, x1, y1), đơn vị point; gốc tọa độ ở góc trên bên trái.")
        print("")

        for page_index in page_indices:
            page = document[page_index]
            page_width = float(page.rect.width)
            page_height = float(page.rect.height)
            blocks = _extract_blocks(page)

            print("-" * 100)
            print(
                f"PAGE {page_index + 1}/{document.page_count} | "
                f"width={page_width:.2f} pt | height={page_height:.2f} pt | "
                f"blocks={len(blocks)}"
            )
            print("-" * 100)

            if not blocks:
                print("[WARNING] Không tìm thấy block văn bản trên trang này.")
                continue

            # In đúng thứ tự _extract_blocks trả về để kiểm tra dữ liệu thô.
            # Không gọi _order_blocks ở đây vì mục tiêu chính là xác minh bbox.
            for index, block in enumerate(blocks):
                total_blocks += 1
                x0, y0, x1, y1 = (
                    float(block["x0"]),
                    float(block["y0"]),
                    float(block["x1"]),
                    float(block["y1"]),
                )
                width = x1 - x0
                height = y1 - y0
                text = " ".join(str(block.get("text", "")).split())

                flags = []
                if x1 < x0 or y1 < y0:
                    invalid_boxes += 1
                    flags.append("INVALID_BBOX")

                tolerance = 1.0  # Cho phép sai số làm tròn nhỏ.
                if (
                    x0 < -tolerance
                    or y0 < -tolerance
                    or x1 > page_width + tolerance
                    or y1 > page_height + tolerance
                ):
                    outside_boxes += 1
                    flags.append("OUTSIDE_PAGE")

                suffix = f"  !! {' | '.join(flags)}" if flags else ""
                print(
                    f"[{index:03d}] "
                    f"bbox=({x0:7.2f}, {y0:7.2f}, {x1:7.2f}, {y1:7.2f}) "
                    f"size=({width:7.2f} x {height:6.2f}){suffix}"
                )
                print(f"      text={text[:240]!r}")

        print("")
        print("=" * 100)
        print("SUMMARY")
        print("=" * 100)
        print(f"Pages checked: {len(page_indices)}")
        print(f"Blocks inspected: {total_blocks}")
        print(f"Invalid bounding boxes: {invalid_boxes}")
        print(f"Blocks outside page bounds: {outside_boxes}")

        if invalid_boxes or outside_boxes:
            print("[RESULT] Có bbox cần kiểm tra.")
            return 1

        print("[RESULT] Không phát hiện bbox bất hợp lệ hoặc nằm ngoài trang.")
        print("Hãy mở PDF và đối chiếu trực quan bbox/text được in phía trên.")
        return 0
    finally:
        document.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="In tọa độ và nội dung từng block trong CV PDF."
    )
    parser.add_argument(
        "pdf",
        nargs="?",
        default=str(DEFAULT_PDF),
        help=f"Đường dẫn PDF (mặc định: {DEFAULT_PDF})",
    )
    parser.add_argument(
        "--page",
        type=int,
        default=None,
        help="Chỉ kiểm tra trang này (đánh số từ 1).",
    )
    args = parser.parse_args()
    return inspect_pdf(Path(args.pdf), args.page)


if __name__ == "__main__":
    raise SystemExit(main())
