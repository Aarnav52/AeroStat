"""Small Gemini tool-calling client for the AeroStat analyst API."""

import logging
import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

from agents.tools.registry import dispatch_tool, get_tool_schemas

logger = logging.getLogger(__name__)
load_dotenv()

ANALYST_SYSTEM_INSTRUCTION = """
You are the AeroStat AI Analyst for India's Airfare Consumer Price Index.

AeroStat's current MVP uses a Jevons index. The base period is the reference
period whose index is 100. CPI values describe relative airfare price movement
against that base period.

Use the minimum number of tools necessary. Simple questions should normally
use one relevant tool. Call additional tools only when their results are
needed to answer the question or verify an interpretation. You may continue
with additional tool calls after reviewing earlier results.

Tool purposes:
- get_latest_cpi: retrieve the most recent CPI/index observation.
- get_cpi_history: retrieve CPI/index observations over a date range.
- compare_cpi_periods: compare CPI/index values between two dates.
- get_route_price_analysis: analyze observed fare changes grouped by route.
- get_airline_price_analysis: analyze observed fare changes grouped by airline.
- get_booking_window_analysis: analyze observed fares by booking window.
- get_cabin_analysis: analyze observed fares by cabin class.
- get_data_quality_summary: summarize data availability and coverage quality.
- get_supporting_observations: retrieve actual cleaned fare observations.
- get_route_details: retrieve metadata for a route.

Database and deterministic tool results are the source of truth. Never invent
values or observations. Do not claim causation unless the available data
directly supports it. Do not call route fare changes CPI contributions unless
a tool explicitly provides contributions. Consider data-quality information
when relevant. If the available tools cannot answer something, say so clearly.
""".strip()


class GeminiClientError(Exception):
    """Raised when Gemini cannot return a usable response."""


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.6-flash",
        timeout: int = 90,
        max_tool_rounds: int = 8,
    ):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_tool_rounds = max_tool_rounds
        self.url = "https://generativelanguage.googleapis.com/v1beta/models/" + self.model + ":generateContent"

    def answer(self, question: str, max_rounds: Optional[int] = None) -> Dict[str, Any]:
        round_limit = max_rounds if max_rounds is not None else self.max_tool_rounds
        contents: List[Dict[str, Any]] = [{"role": "user", "parts": [{"text": question}]}]
        tool_calls: List[Dict[str, Any]] = []
        for _ in range(round_limit):
            candidate = self._generate(contents).get("candidates", [None])[0]
            if not candidate:
                raise GeminiClientError("Gemini returned no candidates")
            parts = candidate.get("content", {}).get("parts", [])
            function_calls = [part["functionCall"] for part in parts if "functionCall" in part]
            if not function_calls:
                answer_text = "\n".join(part.get("text", "") for part in parts).strip()
                if not answer_text:
                    raise GeminiClientError("Gemini returned neither text nor a function call")
                return {"answer": answer_text, "tool_calls": tool_calls}

            contents.append(candidate["content"])
            response_parts = []
            for function_call in function_calls:
                name = function_call.get("name", "")
                arguments = function_call.get("args", {}) or {}
                logger.info("Gemini requested analyst tool=%s arguments=%s", name, arguments)
                result = dispatch_tool(name, arguments)
                tool_calls.append({"tool_name": name, "arguments": arguments, "result": result})
                response_parts.append(
                    {
                        "functionResponse": {
                            "name": name,
                            "response": {"result": result},
                        }
                    }
                )
            contents.append({"role": "user", "parts": response_parts})
        raise GeminiClientError("Gemini exceeded the maximum number of tool-calling rounds")

    def _generate(self, contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        payload = {
            "systemInstruction": {"parts": [{"text": ANALYST_SYSTEM_INSTRUCTION}]},
            "contents": contents,
            "tools": [{"functionDeclarations": get_tool_schemas()}],
        }
        try:
            response = requests.post(self.url, params={"key": self.api_key}, json=payload, timeout=self.timeout)
        except requests.RequestException as exc:
            raise GeminiClientError(f"Gemini request failed: {exc}") from exc
        if not response.ok:
            raise GeminiClientError(f"Gemini API returned HTTP {response.status_code}: {response.text[:500]}")
        try:
            return response.json()
        except ValueError as exc:
            raise GeminiClientError("Gemini API returned invalid JSON") from exc


def get_configured_gemini_client() -> GeminiClient:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GeminiClientError("GEMINI_API_KEY is not configured")
    configured_rounds = os.getenv("GEMINI_MAX_TOOL_ROUNDS", "8")
    try:
        max_tool_rounds = int(configured_rounds)
    except ValueError as exc:
        raise GeminiClientError("GEMINI_MAX_TOOL_ROUNDS must be an integer") from exc
    if max_tool_rounds < 1:
        raise GeminiClientError("GEMINI_MAX_TOOL_ROUNDS must be at least 1")

    return GeminiClient(
        api_key=api_key,
        model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        max_tool_rounds=max_tool_rounds,
    )
