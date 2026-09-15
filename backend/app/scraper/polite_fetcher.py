"""
PoliteFetcher: the shared, compliance-first HTTP fetch layer every
source-specific adapter must go through - no adapter gets its own direct
requests (per CODING_AGENT_CONTEXT.md's spec).

Built step by step. This file currently covers steps 1-2: robots.txt
enforcement and bot-challenge detection, both routed through the same
request path. Per-host rate limiting and the circuit breaker land in
later steps.
"""

import urllib.robotparser
from urllib.parse import urlparse


class RobotsDisallowedError(Exception):
    """robots.txt policy disallows this URL. Never caught and retried - abort."""


class BotChallengeDetectedError(Exception):
    """Response looks like a bot-challenge or block. Never solved, never
    retried, never evaded - abort immediately."""


_BOT_CHALLENGE_STATUS_CODES = {403, 429, 503}

_BOT_CHALLENGE_MARKERS = (
    "captcha",
    "unusual traffic",
    "checking your browser",
    "cloudflare",
    "incapsula",
    "are you a human",
    "please verify you are a human",
    "distil",
    "perimeterx",
)


def _looks_like_bot_challenge(result):
    if result.status_code in _BOT_CHALLENGE_STATUS_CODES:
        return True
    lowered = result.text.lower()
    return any(marker in lowered for marker in _BOT_CHALLENGE_MARKERS)


class FetchResult:
    def __init__(self, url, status_code, text, headers=None):
        self.url = url
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}


class PoliteFetcher:
    """
    Every fetch goes through fetch(). robots.txt is checked before every
    request, fetched via the exact same transport call as any other URL -
    never a library's own auto-fetching reader (RobotFileParser.read()
    makes its own separate network call, silently bypassing whatever
    accounting a shared fetch path does - the gotcha CODING_AGENT_CONTEXT.md
    calls out explicitly).

    There is no way to disable the robots.txt check: no constructor
    parameter exists for it. Passing one anyway raises TypeError, Python's
    ordinary behavior for an unexpected keyword argument - not a config
    flag that could be flipped on by mistake.
    """

    def __init__(self, transport):
        self._transport = transport
        self._robots_cache = {}  # host -> urllib.robotparser.RobotFileParser

    def _robots_url(self, host):
        return f"https://{host}/robots.txt"

    def _do_request(self, url):
        """The one place that actually calls the transport. Every fetch -
        robots.txt included - goes through here, so bot-challenge detection
        applies uniformly rather than only to "real" content fetches."""
        result = self._transport.get(url)
        if _looks_like_bot_challenge(result):
            raise BotChallengeDetectedError(
                f"bot-challenge detected fetching {url} (status={result.status_code})"
            )
        return result

    def _get_robots_parser(self, host):
        if host in self._robots_cache:
            return self._robots_cache[host]

        result = self._do_request(self._robots_url(host))
        parser = urllib.robotparser.RobotFileParser()

        if result.status_code == 200:
            # .parse() on text we fetched ourselves - never .read(), which
            # would fetch again on its own and skip our request path.
            parser.parse(result.text.splitlines())
        elif result.status_code == 401:
            # Access denied to robots.txt itself (but not a bot-challenge
            # status - those already raised above): treat as disallowed,
            # not as wide open.
            parser.disallow_all = True
        else:
            # No robots.txt published (404 etc.) = no rules = allowed.
            parser.allow_all = True

        self._robots_cache[host] = parser
        return parser

    def fetch(self, url, user_agent="APIx-PoliteFetcher/1.0"):
        host = urlparse(url).netloc
        parser = self._get_robots_parser(host)

        if not parser.can_fetch(user_agent, url):
            raise RobotsDisallowedError(f"robots.txt disallows fetching {url}")

        return self._do_request(url)
