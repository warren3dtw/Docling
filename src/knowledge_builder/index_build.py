from __future__ import annotations

import json
from pathlib import Path

from .state import atomic_write_text


def build_indexes(output_dir: Path, document: dict, chapters: list[dict], warnings: list[str]) -> None:
    readme = [f"# {document['filename']}", "", f"- 文件 ID：`{document['document_id']}`", f"- 頁數：{document['page_count']}", f"- SHA-256：`{document['sha256']}`", "", "## 章節", ""]
    index = ["# 文件索引", ""]
    chunks: list[str] = []
    for chapter in chapters:
        rel = chapter.get("source_path", f"chapters/{chapter['chapter_id']}.md")
        pages = chapter["source_pages"]
        readme.append(f"- [{chapter['title']}]({rel})（第 {pages[0]}–{pages[-1]} 頁）")
        index.extend([f"## [{chapter['title']}]({rel})", "", f"- 頁碼：{pages[0]}–{pages[-1]}", f"- 關鍵字：{', '.join(chapter['keywords']) or '無'}", f"- 狀態：{chapter['processing_status']}", ""])
        chunks.append(json.dumps({
            "chunk_id": f"{document['document_id']}:{chapter['chapter_id']}:001",
            "document_id": document["document_id"], "chapter_id": chapter["chapter_id"],
            "text": chapter["text"], "headings": [chapter["title"]], "page_numbers": pages,
            "image_ids": chapter["image_ids"], "source_path": rel,
        }, ensure_ascii=False))
    readme += ["", "## 已知問題與完整性", ""] + ([f"- {warning}" for warning in warnings] or ["- 未偵測到結構性警告；仍建議人工抽驗技術內容。"])
    atomic_write_text(output_dir / "README.md", "\n".join(readme) + "\n")
    atomic_write_text(output_dir / "INDEX.md", "\n".join(index) + "\n")
    atomic_write_text(output_dir / "chunks.jsonl", "\n".join(chunks) + ("\n" if chunks else ""))
