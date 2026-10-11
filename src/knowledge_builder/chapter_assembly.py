from __future__ import annotations

import re


def assemble_chapters(pages: list[dict], fallback_pages: int = 10, max_pages_per_chapter: int = 100) -> list[dict]:
    """Build chapters after all batches are loaded, so batch boundaries have no semantic meaning."""
    chapters: list[dict] = []
    current: dict | None = None
    for page in sorted(pages, key=lambda value: value["page_number"]):
        title = next((h.strip() for h in page.get("headings", []) if h.strip()), None)
        if title and current and title.casefold() != current["title"].casefold():
            current = None
        if current is None:
            number = len(chapters) + 1
            current = {"chapter_id": f"ch-{number:03d}", "title": title or f"第 {page['page_number']} 頁起", "source_pages": [], "parts": [], "image_ids": []}
            chapters.append(current)
        current["source_pages"].append(page["page_number"])
        if page.get("text"):
            current["parts"].append(page["text"])
        current["parts"].extend(page.get("tables", []))
        if len(current["source_pages"]) >= max_pages_per_chapter:
            current = None
            continue
        if not title and len(current["source_pages"]) >= fallback_pages:
            current = None
    for chapter in chapters:
        chapter["text"] = "\n\n".join(dict.fromkeys(part.strip() for part in chapter.pop("parts") if part.strip()))
        chapter["keywords"] = _extractive_keywords(chapter["title"], chapter["text"])
        chapter["summary"] = None
        chapter["search_questions"] = []
        chapter["processing_status"] = "pending_enrichment"
    return chapters


def _extractive_keywords(title: str, text: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|[\u4e00-\u9fff]{2,8}", title + " " + text[:2000])
    counts: dict[str, int] = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    return [word for word, _ in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[:12]]
