from __future__ import annotations

from pathlib import Path

import yaml

from .state import atomic_write_text


def export_chapters(output_dir: Path, document: dict, chapters: list[dict], images: list[dict]) -> None:
    chapter_dir = output_dir / "chapters"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    by_page: dict[int, list[dict]] = {}
    for image in images:
        by_page.setdefault(image["source_page"], []).append(image)
    for index, chapter in enumerate(chapters):
        chapter_images = [img for page in chapter["source_pages"] for img in by_page.get(page, [])]
        chapter["image_ids"] = [img["image_id"] for img in chapter_images]
        related = []
        if index:
            related.append(chapters[index - 1]["chapter_id"])
        if index + 1 < len(chapters):
            related.append(chapters[index + 1]["chapter_id"])
        frontmatter = {
            "document_id": document["document_id"], "chapter_id": chapter["chapter_id"],
            "source_file": document["filename"], "source_pages": chapter["source_pages"],
            "title": chapter["title"], "summary": chapter["summary"], "keywords": chapter["keywords"],
            "search_questions": chapter["search_questions"], "related_chapters": related,
            "images": chapter["image_ids"], "processing_status": chapter["processing_status"],
        }
        start, end = chapter["source_pages"][0], chapter["source_pages"][-1]
        lines = ["---", yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).rstrip(), "---", "", f"# {chapter['title']}", "", f"> 來源：{document['filename']}，原始 PDF 第 {start}–{end} 頁。", ""]
        if chapter["summary"]:
            lines += ["## 本章摘要", "", chapter["summary"], ""]
        lines += ["## 原始內容", "", chapter["text"] or "_本頁未擷取到可讀文字。_", ""]
        for image in chapter_images:
            lines += [f"![{image['caption_original'] or image['image_id']}]({image['image_path']})", ""]
            if image.get("caption_vlm"):
                lines += [f"**圖片 AI 描述**：{image['caption_vlm']}", ""]
        if related:
            lines += ["## 相關章節", ""] + [f"- [{cid}]({cid}.md)" for cid in related] + [""]
        atomic_write_text(chapter_dir / f"{chapter['chapter_id']}.md", "\n".join(lines))
