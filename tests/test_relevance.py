from zotero_mcp.relevance import score_text_match, score_creators_match, score_recency, rank_results


def test_exact_match_scores_highest():
    assert score_text_match("Machine Learning", "machine learning") == 1.0


def test_starts_with_match():
    assert score_text_match("Machine", "Machine Learning Basics") == 0.7


def test_contains_match():
    assert score_text_match("Learning", "Deep Learning Systems") == 0.5


def test_word_overlap():
    score = score_text_match("quantum machine learning", "introduction to machine learning")
    assert 0.0 < score < 0.5  # partial word overlap


def test_no_match_scores_zero():
    assert score_text_match("quantum", "biology review") == 0.0


def test_empty_inputs():
    assert score_text_match("", "something") == 0.0
    assert score_text_match("something", "") == 0.0


def test_creators_match():
    creators = [
        {"firstName": "Jane", "lastName": "Doe", "creatorType": "author"},
        {"firstName": "John", "lastName": "Smith", "creatorType": "author"},
    ]
    assert score_creators_match("Jane Doe", creators) == 1.0
    assert score_creators_match("Smith", creators) > 0.0
    assert score_creators_match("Unknown Person", creators) == 0.0


def test_creators_match_empty():
    assert score_creators_match("Jane", []) == 0.0


def test_recency_boost_current_year():
    score = score_recency("2026")
    assert score == 0.1  # max_boost default


def test_recency_boost_old():
    assert score_recency("1999") == 0.0
    assert score_recency("2000") == 0.0


def test_recency_boost_mid():
    score = score_recency("2013")
    assert 0.0 < score < 0.1


def test_recency_boost_none():
    assert score_recency(None) == 0.0
    assert score_recency("no date") == 0.0


def test_rank_results_ordering():
    items = [
        {"key": "A", "data": {"title": "Introduction to Biology", "date": "2020", "creators": []}},
        {"key": "B", "data": {"title": "Machine Learning Basics", "date": "2020", "creators": []}},
        {"key": "C", "data": {"title": "Advanced Machine Learning", "date": "2020", "creators": []}},
    ]
    ranked = rank_results("Machine Learning", items, search_fields=["title"])
    # Exact-ish match should be first
    assert ranked[0][0]["key"] == "B"  # "Machine Learning Basics" starts with query
    assert ranked[1][0]["key"] == "C"  # contains "Machine Learning"
    assert ranked[2][0]["key"] == "A"  # word overlap only ("introduction" doesn't match)
    # All scores in 0-1
    for _, score in ranked:
        assert 0.0 <= score <= 1.0


def test_rank_results_empty():
    assert rank_results("query", [], search_fields=["title"]) == []
