"""Small Gemini tool-calling client for the AeroStat analyst API."""

import logging
import os
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

from agents.tools.registry import dispatch_tool, get_tool_schemas

logger = logging.getLogger(__name__)
load_dotenv()


class GeminiClientError(Exception):
    """Raised when Gemini cannot return a usable response."""


class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash", timeout: int = 90):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.url = "https://generativelanguage.googleapis.com/v1beta/models/" + self.model + ":generateContent"

    def answer(self, question: str, max_rounds: int = 8) -> Dict[str, Any]:
        contents: List[Dict[str, Any]] = [{"role": "user", "parts": [{"text": question}]}]
        tool_calls: List[Dict[str, Any]] = []
        for _ in range(max_rounds):
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
                response_parts.append({"functionResponse": {"name": name, "response": result}})
            contents.append({"role": "user", "parts": response_parts})
        raise GeminiClientError("Gemini exceeded the maximum number of tool-calling rounds")

    def _generate(self, contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        payload = {"contents": contents, "tools": [{"functionDeclarations": get_tool_schemas()}]}
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
    return GeminiClient(api_key=api_key, model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
