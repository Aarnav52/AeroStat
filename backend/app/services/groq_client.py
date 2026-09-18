"""Small Groq tool-calling client for the AeroStat analyst API."""

import json
import logging
import os
from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional, cast

from dotenv import load_dotenv
from groq import Groq
from groq.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam

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


class GroqClientError(Exception):
    """Raised when Groq cannot return a usable response."""


class GroqAnalystClient:
    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-oss-120b",
        timeout: int = 90,
        max_tool_rounds: int = 8,
    ):
        self.client = Groq(api_key=api_key, timeout=timeout)
        self.model = model
        self.max_tool_rounds = max_tool_rounds

    def answer(self, question: str, max_rounds: Optional[int] = None) -> Dict[str, Any]:
        round_limit = max_rounds if max_rounds is not None else self.max_tool_rounds
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": ANALYST_SYSTEM_INSTRUCTION},
            {"role": "user", "content": question},
        ]
        tool_calls: List[Dict[str, Any]] = []

        for _ in range(round_limit):
            message = self._generate(messages)
            requested_tools = getattr(message, "tool_calls", None) or []
            if not requested_tools:
                answer_text = getattr(message, "content", None) or ""
                if not isinstance(answer_text, str) or not answer_text.strip():
                    raise GroqClientError("Groq returned neither text nor a tool call")
                messages.append({"role": "assistant", "content": answer_text.strip()})
                final_message = self._generate_final(messages)
                final_text = getattr(final_message, "content", None) or ""
                if not isinstance(final_text, str) or not final_text.strip():
                    raise GroqClientError("Groq returned an empty final response")
                return self._format_response(final_text.strip(), tool_calls)

            assistant_message = {
                "role": "assistant",
                "content": getattr(message, "content", None),
                "tool_calls": [self._tool_call_to_dict(tool_call) for tool_call in requested_tools],
            }
            messages.append(assistant_message)

            for tool_call in requested_tools:
                function = getattr(tool_call, "function", None)
                name = getattr(function, "name", "")
                raw_arguments = getattr(function, "arguments", "{}")
                arguments = self._parse_arguments(raw_arguments, name)
                arguments = self._remove_null_optional_arguments(arguments)
                logger.info("Groq requested analyst tool=%s arguments=%s", name, arguments)
                result = dispatch_tool(name, arguments)
                tool_calls.append({"tool_name": name, "arguments": arguments, "result": result})
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": getattr(tool_call, "id", ""),
                        "content": json.dumps(result),
                    }
                )

        raise GroqClientError("Groq exceeded the maximum number of tool-calling rounds")

    def _generate(self, messages: List[Dict[str, Any]]) -> Any:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=cast(Iterable[ChatCompletionMessageParam], messages),
                tools=cast(
                    Iterable[ChatCompletionToolParam],
                    [
                        {
                            "type": "function",
                            "function": schema,
                        }
                        for schema in self._get_groq_tool_schemas()
                    ],
                ),
                tool_choice="auto",
            )
        except Exception as exc:
            raise GroqClientError(f"Groq request failed: {exc}") from exc

        choices = getattr(response, "choices", [])
        if not choices or getattr(choices[0], "message", None) is None:
            raise GroqClientError("Groq returned no usable response")
        return choices[0].message

    def _generate_final(self, messages: List[Dict[str, Any]]) -> Any:
        final_messages = list(messages)
        final_messages.append(
            {
                "role": "user",
                "content": (
                    "Return ONLY a valid JSON object matching this exact Stage D "
                    "structure: {\"answer\": \"...\", \"key_findings\": [], "
                    "\"evidence\": [], \"limitations\": [], \"tool_calls\": []}. "
                    "Use the available tool results as the source of truth. "
                    "Do not call tools in this final response. Keep simple factual "
                    "answers concise and include limitations only when relevant."
                ),
            }
        )
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=cast(Iterable[ChatCompletionMessageParam], final_messages),
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            raise GroqClientError(f"Groq final response failed: {exc}") from exc

        choices = getattr(response, "choices", [])
        if not choices or getattr(choices[0], "message", None) is None:
            raise GroqClientError("Groq returned no usable final response")
        return choices[0].message

    @staticmethod
    def _get_groq_tool_schemas() -> List[Dict[str, Any]]:
        """Adapt registry schemas without changing the provider-agnostic registry."""
        groq_schemas = []
        for schema in get_tool_schemas():
            schema_copy = deepcopy(schema)
            properties = schema_copy.get("parameters", {}).get("properties", {})
            required = schema_copy.get("parameters", {}).get("required", [])
            schema_copy["parameters"]["required"] = [
                name for name in required if name in properties
            ]
            for name, property_schema in properties.items():
                if name not in required and property_schema.get("type") == "string":
                    property_schema["type"] = ["string", "null"]
            groq_schemas.append(schema_copy)
        return groq_schemas

    @staticmethod
    def _parse_arguments(raw_arguments: Any, tool_name: str) -> Dict[str, Any]:
        if isinstance(raw_arguments, dict):
            return raw_arguments
        try:
            arguments = json.loads(raw_arguments or "{}")
        except (TypeError, ValueError) as exc:
            raise GroqClientError(
                f"Groq returned malformed arguments for tool '{tool_name}'"
            ) from exc
        if not isinstance(arguments, dict):
            raise GroqClientError(f"Groq arguments for tool '{tool_name}' must be an object")
        return arguments

    @staticmethod
    def _remove_null_optional_arguments(arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Treat explicit null optional arguments as omitted Python arguments."""
        return {
            name: value
            for name, value in arguments.items()
            if value is not None
        }

    @staticmethod
    def _tool_call_to_dict(tool_call: Any) -> Dict[str, Any]:
        function = getattr(tool_call, "function", None)
        return {
            "id": getattr(tool_call, "id", ""),
            "type": getattr(tool_call, "type", "function"),
            "function": {
                "name": getattr(function, "name", ""),
                "arguments": getattr(function, "arguments", "{}"),
            },
        }

    @staticmethod
    def _format_response(answer_text: str, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        parsed_response = GroqAnalystClient._parse_json_response(answer_text)
        if parsed_response is None:
            response = {
                "answer": answer_text,
                "key_findings": [],
                "evidence": [{"tool": call["tool_name"]} for call in tool_calls],
                "limitations": [],
            }
        else:
            response = {
                "answer": parsed_response.get("answer")
                if isinstance(parsed_response.get("answer"), str)
                else answer_text,
                "key_findings": parsed_response.get("key_findings")
                if isinstance(parsed_response.get("key_findings"), list)
                else [],
                "evidence": parsed_response.get("evidence")
                if isinstance(parsed_response.get("evidence"), list)
                else [],
                "limitations": parsed_response.get("limitations")
                if isinstance(parsed_response.get("limitations"), list)
                else [],
            }
        response["tool_calls"] = tool_calls
        return response

    @staticmethod
    def _parse_json_response(answer_text: str) -> Optional[Dict[str, Any]]:
        candidate_text = answer_text.strip()
        if candidate_text.startswith("```"):
            candidate_text = candidate_text.strip("`").strip()
            if candidate_text.startswith("json"):
                candidate_text = candidate_text[4:].strip()
        try:
            parsed_response = json.loads(candidate_text)
        except (TypeError, ValueError):
            return None
        if not isinstance(parsed_response, dict):
            return None
        return parsed_response


def get_configured_groq_client() -> GroqAnalystClient:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise GroqClientError("GROQ_API_KEY is not configured")

    configured_rounds = os.getenv("GROQ_MAX_TOOL_ROUNDS", "8")
    try:
        max_tool_rounds = int(configured_rounds)
    except ValueError as exc:
        raise GroqClientError("GROQ_MAX_TOOL_ROUNDS must be an integer") from exc
    if max_tool_rounds < 1:
        raise GroqClientError("GROQ_MAX_TOOL_ROUNDS must be at least 1")

    return GroqAnalystClient(
        api_key=api_key,
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        max_tool_rounds=max_tool_rounds,
    )
