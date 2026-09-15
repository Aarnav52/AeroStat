"""
Self-check for PoliteFetcher step 1 (robots.txt enforcement).
Plain asserts, no framework, no real network - a FakeTransport stands in
for HTTP. Run directly: python test_polite_fetcher.py
"""

from app.scraper.polite_fetcher import (
    PoliteFetcher,
    RobotsDisallowedError,
    BotChallengeDetectedError,
    FetchResult,
)


class FakeTransport:
    """Canned responses keyed by exact URL. Records every call made, so
    tests can prove robots.txt goes through this same path, not some
    separate hidden fetch."""

    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get(self, url):
        self.calls.append(url)
        if url not in self.responses:
            raise AssertionError(f"unexpected fetch: {url}")
        return self.responses[url]


def test_disallowed_path_raises():
    transport = FakeTransport({
        "https://example.com/robots.txt": FetchResult(
            "https://example.com/robots.txt", 200,
            "User-agent: *\nDisallow: /private/\n",
        ),
    })
    fetcher = PoliteFetcher(transport)
    try:
        fetcher.fetch("https://example.com/private/secret")
        raise AssertionError("expected RobotsDisallowedError")
    except RobotsDisallowedError:
        pass


def test_allowed_path_succeeds():
    transport = FakeTransport({
        "https://example.com/robots.txt": FetchResult(
            "https://example.com/robots.txt", 200,
            "User-agent: *\nDisallow: /private/\n",
        ),
        "https://example.com/public/page": FetchResult(
            "https://example.com/public/page", 200, "hello",
        ),
    })
    fetcher = PoliteFetcher(transport)
    result = fetcher.fetch("https://example.com/public/page")
    assert result.text == "hello"


def test_robots_txt_fetched_through_same_transport():
    transport = FakeTransport({
        "https://example.com/robots.txt": FetchResult(
            "https://example.com/robots.txt", 200, "User-agent: *\nAllow: /\n",
        ),
        "https://example.com/page": FetchResult(
            "https://example.com/page", 200, "ok",
        ),
    })
    fetcher = PoliteFetcher(transport)
    fetcher.fetch("https://example.com/page")
    assert transport.calls == [
        "https://example.com/robots.txt",
        "https://example.com/page",
    ], transport.calls


def test_robots_txt_cached_not_refetched():
    transport = FakeTransport({
        "https://example.com/robots.txt": FetchResult(
            "https://example.com/robots.txt", 200, "User-agent: *\nAllow: /\n",
        ),
        "https://example.com/a": FetchResult("https://example.com/a", 200, "a"),
        "https://example.com/b": FetchResult("https://example.com/b", 200, "b"),
    })
    fetcher = PoliteFetcher(transport)
    fetcher.fetch("https://example.com/a")
    fetcher.fetch("https://example.com/b")
    robots_fetches = [c for c in transport.calls if c.endswith("/robots.txt")]
    assert len(robots_fetches) == 1, robots_fetches


def test_missing_robots_txt_means_allowed():
    transport = FakeTransport({
        "https://example.com/robots.txt": FetchResult(
            "https://example.com/robots.txt", 404, "",
        ),
        "https://example.com/page": FetchResult(
            "https://example.com/page", 200, "ok",
        ),
    })
    fetcher = PoliteFetcher(transport)
    result = fetcher.fetch("https://example.com/page")
    assert result.text == "ok"


def test_robots_txt_401_means_disallow_all():
    # 401 isn't one of the bot-challenge status codes (403/429/503) - it's
    # a distinct "access denied" signal, handled as a robots.txt policy
    # matter, not a bot-challenge.
    transport = FakeTransport({
        "https://example.com/robots.txt": FetchResult(
            "https://example.com/robots.txt", 401, "",
        ),
    })
    fetcher = PoliteFetcher(transport)
    try:
        fetcher.fetch("https://example.com/anything")
        raise AssertionError("expected RobotsDisallowedError")
    except RobotsDisallowedError:
        pass


def test_robots_txt_403_is_a_bot_challenge_not_a_policy_disallow():
    # 403 IS one of the named bot-challenge status codes - getting blocked
    # while fetching robots.txt itself is a different situation than the
    # site's policy saying no, and must be distinguished.
    transport = FakeTransport({
        "https://example.com/robots.txt": FetchResult(
            "https://example.com/robots.txt", 403, "",
        ),
    })
    fetcher = PoliteFetcher(transport)
    try:
        fetcher.fetch("https://example.com/anything")
        raise AssertionError("expected BotChallengeDetectedError")
    except BotChallengeDetectedError:
        pass


def test_bot_challenge_status_code_raises_and_is_not_retried():
    transport = FakeTransport({
        "https://example.com/robots.txt": FetchResult(
            "https://example.com/robots.txt", 200, "User-agent: *\nAllow: /\n",
        ),
        "https://example.com/page": FetchResult(
            "https://example.com/page", 429, "slow down",
        ),
    })
    fetcher = PoliteFetcher(transport)
    try:
        fetcher.fetch("https://example.com/page")
        raise AssertionError("expected BotChallengeDetectedError")
    except BotChallengeDetectedError:
        pass
    page_fetches = [c for c in transport.calls if c == "https://example.com/page"]
    assert len(page_fetches) == 1, "must not retry after a bot-challenge"


def test_bot_challenge_text_marker_raises_even_on_200():
    transport = FakeTransport({
        "https://example.com/robots.txt": FetchResult(
            "https://example.com/robots.txt", 200, "User-agent: *\nAllow: /\n",
        ),
        "https://example.com/page": FetchResult(
            "https://example.com/page", 200,
            "<html>Please complete the CAPTCHA to continue</html>",
        ),
    })
    fetcher = PoliteFetcher(transport)
    try:
        fetcher.fetch("https://example.com/page")
        raise AssertionError("expected BotChallengeDetectedError")
    except BotChallengeDetectedError:
        pass


def test_cannot_disable_robots_check():
    transport = FakeTransport({})
    try:
        PoliteFetcher(transport, respect_robots_txt=False)
        raise AssertionError("expected TypeError - no such parameter exists")
    except TypeError:
        pass


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
    print(f"\n{len(tests)} tests passed.")
