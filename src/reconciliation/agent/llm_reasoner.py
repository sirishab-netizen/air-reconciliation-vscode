import json
import os
from time import perf_counter

from dotenv import load_dotenv
from openai import OpenAI

from .models import ReasoningResult


load_dotenv()


class LLMReasoner:
    def __init__(
        self,
        tools=None,
        trace=None,
        model="gpt-5.6-luna",
    ):
        self.tools = tools
        self.trace = trace
        self.model = model

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not configured."
            )

        self.client = OpenAI(api_key=api_key)

    def reason(
        self,
        exception_type: str,
        evidence: dict,
    ) -> ReasoningResult:

        reasoning_start = perf_counter()

        if self.trace:
            self.trace.add(
                "REASONING",
                f"LLM reasoning started using {self.model}",
            )

        instructions = """
You are a financial reconciliation investigation assistant.

Your role is to investigate reconciliation exceptions using
authoritative evidence retrieved through read-only tools.

Rules:

1. Treat deterministic reconciliation results as authoritative.
2. Never change or recalculate financial facts.
3. Use read-only tools when additional evidence is required.
4. Never invent records, transactions, explanations, or business rules.
5. Clearly distinguish factual findings from hypotheses.
6. If evidence is insufficient to determine the root cause,
   explicitly say so.
7. A discrepancy can have HIGH finding confidence even when
   root-cause confidence is LOW.
8. Never recommend an automatic financial adjustment.
9. Financial changes always require human approval.
10. Return the final answer as JSON.

The JSON must contain exactly these fields:

{
  "findings": ["..."],
  "hypothesis": "...",
  "finding_confidence": "HIGH|MEDIUM|LOW",
  "root_cause_confidence": "HIGH|MEDIUM|LOW",
  "recommendation": "...",
  "requires_human_approval": true
}
"""

        user_input = {
            "exception_type": exception_type,
            "evidence": evidence,
        }

        messages = [
            {
                "role": "user",
                "content": json.dumps(
                    user_input,
                    default=str,
                ),
            }
        ]

        tool_definitions = []

        if self.tools:
            tool_definitions = (
                self.tools.get_tool_definitions()
            )

        max_iterations = 5
        llm_call_count = 0

        for iteration in range(max_iterations):

            llm_start = perf_counter()

            response = self.client.responses.create(
                model=self.model,
                instructions=instructions,
                input=messages,
                tools=tool_definitions,
            )

            llm_duration_ms = (
                perf_counter() - llm_start
            ) * 1000

            llm_call_count += 1

            if self.trace:
                self.trace.add(
                    "LLM",
                    f"LLM call {llm_call_count} completed",
                    duration_ms=llm_duration_ms,
                )

            tool_calls = []

            for item in response.output:
                if item.type == "function_call":
                    tool_calls.append(item)

            # No more tool calls means the LLM has
            # produced its final reasoning result.
            if not tool_calls:

                result = self._parse_result(
                    response.output_text
                )

                total_reasoning_ms = (
                    perf_counter() - reasoning_start
                ) * 1000

                if self.trace:
                    self.trace.add(
                        "REASONING",
                        (
                            "LLM reasoning completed "
                            f"after {llm_call_count} "
                            "LLM call(s)"
                        ),
                        duration_ms=total_reasoning_ms,
                    )

                return result

            # Execute requested read-only tools.
            for tool_call in tool_calls:

                arguments = json.loads(
                    tool_call.arguments
                )

                tool_name = tool_call.name

                tool_result = self._execute_tool(
                    tool_name,
                    arguments,
                )

                # Add the function call to the
                # conversation history.
                messages.append(
                    {
                        "type": "function_call",
                        "call_id": tool_call.call_id,
                        "name": tool_name,
                        "arguments": tool_call.arguments,
                    }
                )

                # Add the tool result.
                messages.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_call.call_id,
                        "output": json.dumps(
                            tool_result,
                            default=str,
                        ),
                    }
                )

        raise RuntimeError(
            "LLM reasoning exceeded the maximum "
            f"number of iterations ({max_iterations})."
        )

    def _execute_tool(
        self,
        tool_name: str,
        arguments: dict,
    ):
        if not self.tools:
            raise RuntimeError(
                "No reconciliation tools are configured."
            )

        booking_id = arguments["booking_id"]

        if tool_name == "get_booking":
            return self.tools.get_booking(
                booking_id
            )

        if tool_name == "get_ticket":
            return self.tools.get_ticket(
                booking_id
            )

        if tool_name == "get_invoice":
            return self.tools.get_invoice(
                booking_id
            )

        if tool_name == "get_settlement":
            return self.tools.get_settlement(
                booking_id
            )

        if tool_name == "get_refund":
            return self.tools.get_refund(
                booking_id
            )

        if tool_name == "get_exchange":
            return self.tools.get_exchange(
                booking_id
            )

        raise ValueError(
            f"Unknown tool requested: {tool_name}"
        )

    def _parse_result(
        self,
        output_text: str,
    ) -> ReasoningResult:

        try:
            data = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "LLM returned invalid JSON."
            ) from exc

        required_fields = [
            "findings",
            "hypothesis",
            "finding_confidence",
            "root_cause_confidence",
            "recommendation",
            "requires_human_approval",
        ]

        missing_fields = [
            field
            for field in required_fields
            if field not in data
        ]

        if missing_fields:
            raise ValueError(
                "LLM response is missing required fields: "
                + ", ".join(missing_fields)
            )

        return ReasoningResult(
            findings=data["findings"],
            hypothesis=data["hypothesis"],
            finding_confidence=data[
                "finding_confidence"
            ],
            root_cause_confidence=data[
                "root_cause_confidence"
            ],
            recommendation=data[
                "recommendation"
            ],
            requires_human_approval=data[
                "requires_human_approval"
            ],
        )