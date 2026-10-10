from pathlib import Path

from src.processing.cv_text_extractor import (
    _extract_blocks,
    _find_column_boundary,
    _order_blocks,
)
import pymupdf


PDF_PATH = Path(
    r"data\Java Intern-CV.pdf"
)


def main():
    if not PDF_PATH.exists():
        print(f"Không tìm thấy file PDF: {PDF_PATH}")
        return

    with pymupdf.open(PDF_PATH) as document:
        for page_number, page in enumerate(document, start=1):
            blocks = _extract_blocks(page)
            boundary = _find_column_boundary(
                blocks,
                page.rect.width,
            )
            ordered_blocks = _order_blocks(
                blocks,
                page.rect.width,
            )

            print(f"\n{'=' * 60}")
            print(f"PAGE {page_number}")
            print(f"Page width: {page.rect.width:.1f}")
            print(f"Detected column boundary: {boundary}")
            print(f"Number of blocks: {len(blocks)}")
            print(f"{'=' * 60}")

            for index, block in enumerate(ordered_blocks, start=1):
                print(
                    f"\n[{index}] "
                    f"x0={block['x0']:.1f}, "
                    f"y0={block['y0']:.1f}, "
                    f"x1={block['x1']:.1f}, "
                    f"y1={block['y1']:.1f}"
                )
                print(block["text"])


if __name__ == "__main__":
    main()