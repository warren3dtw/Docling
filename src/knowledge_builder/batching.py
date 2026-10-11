from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PageBatch:
    batch_id: str
    start_page: int
    end_page: int

    @property
    def page_count(self) -> int:
        return self.end_page - self.start_page + 1

    def to_dict(self) -> dict:
        return asdict(self)


def make_batches(total_pages: int, pages_per_batch: int) -> list[PageBatch]:
    if total_pages < 0 or pages_per_batch < 1:
        raise ValueError("頁數不可為負，且每批頁數必須至少為 1")
    return [
        PageBatch(f"batch-{start:05d}-{min(start + pages_per_batch - 1, total_pages):05d}", start, min(start + pages_per_batch - 1, total_pages))
        for start in range(1, total_pages + 1, pages_per_batch)
    ]
