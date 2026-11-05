import html
import re

def clean_job_description(text: str) -> str:
    """Convert encoded HTML job description into clean plain text."""
    if not text:
        return ""

    # Decode HTML entities (ví dụ: &amp; -> &)
    text = html.unescape(text)

    # Giữ lại xuống dòng cho các thẻ block
    text = re.sub(r"<\s*(?:br|hr)\b[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<\s*/?\s*(?:p|div|li|h[1-6]|tr|ul|ol|section|article)\b[^>]*>", "\n", text, flags=re.IGNORECASE)

    # Xóa các thẻ HTML còn lại
    text = re.sub(r"<[^>]+>", "", text)

    # Xóa các ký tự Markdown thừa
    text = re.sub(r"\*\*|__", "", text)
    text = re.sub(r"(?<!\w)[*_]|[*_](?!\w)", "", text)

    # Chuẩn hóa khoảng trắng
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", text)

    return text.strip()