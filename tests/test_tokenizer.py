from glyph.source.tokenizer import count_tokens, fallback_tokens


def test_fallback_tokenizer_counts_words_and_symbols():
    assert fallback_tokens("must[run_tests_before_done]") == ["must", "[", "run_tests_before_done", "]"]
    count, name = count_tokens("hello, world")
    assert count >= 3
    assert name
