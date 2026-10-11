"""Create a small, non-sensitive PDF for a manual smoke test."""

from pathlib import Path

import pymupdf as fitz


def main() -> None:
    target = Path("data/input/sample.pdf")
    target.parent.mkdir(parents=True, exist_ok=True)
    document = fitz.open()
    for number in range(1, 4):
        page = document.new_page()
        if number == 1:
            page.insert_text((72, 72), "Sample Knowledge Document", fontsize=20)
        page.insert_text((72, 110), f"This is synthetic page {number}; it contains no private data.", fontsize=11)
    document.save(target)
    document.close()
    print(f"Created {target}")


if __name__ == "__main__":
    main()
