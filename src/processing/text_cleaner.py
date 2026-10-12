
import html
import re


def clean_job_description(text: str) -> str:
    """Convert encoded HTML job description into clean plain text."""
    if not text:
        return ""

    # Decode HTML entities.
    text = html.unescape(text)

    # Preserve HTML block boundaries before removing tags.
    text = re.sub(
        r"<\s*(?:br|hr)\b[^>]*>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"<\s*/?\s*(?:p|div|li|h[1-6]|tr|ul|ol|section|article)\b[^>]*>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    # Remove remaining HTML tags.
    text = re.sub(r"<[^>]+>", "", text)

    # Remove common Markdown emphasis markers.
    text = re.sub(r"\*\*|__", "", text)
    text = re.sub(r"(?<!\w)[*_]|[*_](?!\w)", "", text)

    # Normalize horizontal whitespace while preserving newlines.
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize excessive blank lines.
    text = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", text)

    return text.strip()
