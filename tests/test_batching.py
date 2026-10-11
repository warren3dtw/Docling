from knowledge_builder.batching import make_batches


def test_23_pages_in_three_batches():
    batches = make_batches(23, 10)
    assert [(b.start_page, b.end_page) for b in batches] == [(1, 10), (11, 20), (21, 23)]
