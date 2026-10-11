from __future__ import annotations

from pathlib import Path

import yaml

from .state import atomic_write_text


def export_chapters(
    output_dir: Path,
    document: dict,
    chapters: list[dict],
    images: list[dict],
    page_images: list[dict] | None = None,
    max_pages_per_file: int = 100,
) -> list[str]:
    chapter_dir = output_dir / "chapters"
    by_page: dict[int, list[dict]] = {}
    for image in images:
        by_page.setdefault(image["source_page"], []).append(image)
    available_page_images = {image["page_number"] for image in (page_images or [])}

    # Chapters remain semantic retrieval units; Markdown files group many chapters
    # so ordinary documents stay readable as one complete file.
    groups: list[list[dict]] = []
    current: list[dict] = []
    current_pages: set[int] = set()
    for chapter in chapters:
        chapter_pages = set(chapter["source_pages"])
        if current and len(current_pages | chapter_pages) > max_pages_per_file:
            groups.append(current)
            current = []
            current_pages = set()
        current.append(chapter)
        current_pages.update(chapter_pages)
    if current:
        groups.append(current)

    filenames = ["DOCUMENT.md"] if len(groups) <= 1 else [f"PART-{index:03d}.md" for index in range(1, len(groups) + 1)]
    if not groups:
        filenames = ["DOCUMENT.md"]
        groups = [[]]

    keep_files = set(filenames)
    for stale_file in [output_dir / "DOCUMENT.md", *output_dir.glob("PART-*.md")]:
        if stale_file.exists() and stale_file.name not in keep_files:
            stale_file.unlink()

    for old_file in chapter_dir.glob("*.md") if chapter_dir.exists() else []:
        old_file.unlink()
    if chapter_dir.exists() and not any(chapter_dir.iterdir()):
        try:
            chapter_dir.rmdir()
        except OSError:
            # A sync client may temporarily hold the now-empty legacy directory.
            pass

    for group_index, (group, filename) in enumerate(zip(groups, filenames), start=1):
        group_pages = sorted({page for chapter in group for page in chapter["source_pages"]})
        group_images = [image for page in group_pages for image in by_page.get(page, [])]
        for chapter in group:
            chapter["image_ids"] = [image["image_id"] for page in chapter["source_pages"] for image in by_page.get(page, [])]
            chapter["source_path"] = f"{filename}#{chapter['chapter_id']}"

        title = group[0]["title"] if len(groups) == 1 and group else document["filename"]
        group_id = "document" if len(groups) == 1 else f"part-{group_index:03d}"
        all_keywords = list(dict.fromkeys(keyword for chapter in group for keyword in chapter["keywords"]))
        frontmatter = {
            "document_id": document["document_id"], "chapter_id": group_id,
            "source_file": document["filename"], "source_pages": group_pages,
            "title": title, "summary": None, "keywords": all_keywords[:40],
            "search_questions": [], "related_chapters": [],
            "images": [image["image_id"] for image in group_images],
            "processing_status": "pending_enrichment" if not group or all(chapter["processing_status"] == "pending_enrichment" for chapter in group) else "enriched",
        }
        if group:
            start, end = group_pages[0], group_pages[-1]
        else:
            start = end = 0
        heading = title if len(groups) == 1 else f"{document['filename']} — 第 {group_index} 部分"
        lines = ["---", yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).rstrip(), "---", "", f"# {heading}", "", f"> 來源：{document['filename']}，原始 PDF 第 {start}–{end} 頁。", ""]
        source_links = [
            f"- [第 {page} 頁](pages/page_{page:04d}.webp)"
            for page in group_pages
            if page in available_page_images
        ]
        if source_links:
            lines += ["## 原始頁面索引", "", *source_links, ""]

        for chapter in group:
            lines += [f"<a id=\"{chapter['chapter_id']}\"></a>", f"## {chapter['title']}", "", f"> 原 PDF 第 {chapter['source_pages'][0]}–{chapter['source_pages'][-1]} 頁。", ""]
            if chapter["summary"]:
                lines += ["### 摘要", "", chapter["summary"], ""]
            lines += [chapter["text"] or "_本頁未擷取到可讀文字。_", ""]
            for page in chapter["source_pages"]:
                for image in by_page.get(page, []):
                    lines += [f"![{image['caption_original'] or image['image_id']}](images/{Path(image['image_path']).name})", ""]
                    if image.get("caption_vlm"):
                        lines += [f"**圖片 AI 描述**：{image['caption_vlm']}", ""]
        atomic_write_text(output_dir / filename, "\n".join(lines))

    return filenames
