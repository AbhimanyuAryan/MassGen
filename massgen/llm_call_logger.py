# -*- coding: utf-8 -*-
"""
LLM Call Logger - Saves all LLM interactions in OpenAI messages format.

Each API call is saved as a JSON file with:
- Input messages (what was sent to the LLM)
- Output (streaming chunks accumulated into final response)
- Metadata (model, tokens, timing, agent_id, call_number)

Usage:
    massgen --save-llm-calls --config config.yaml "Your question"
    massgen --save-llm-calls --save-llm-chunks --config config.yaml "Your question"

Output files are saved to:
    .massgen/massgen_logs/log_TIMESTAMP/turn_N/attempt_N/llm_calls/AGENT_call_NNN.json
"""

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from loguru import logger


@dataclass
class LLMCallRecord:
    """Record of a single LLM API call."""

    call_id: str
    agent_id: str
    backend_name: str
    model: str

    # Input
    messages: List[Dict[str, Any]]
    tools: List[Dict[str, Any]]

    # Output (accumulated from streaming)
    output_content: str = ""
    output_tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    output_reasoning: str = ""
    finish_reason: str = ""

    # Timing
    start_time: float = 0.0
    end_time: float = 0.0
    first_chunk_time: float = 0.0

    # Tokens
    input_tokens: int = 0
    output_tokens: int = 0

    # Streaming details
    chunk_count: int = 0
    chunks: List[Dict[str, Any]] = field(default_factory=list)  # Optional detailed chunks

    def to_openai_format(self, include_chunks: bool = False) -> Dict[str, Any]:
        """Convert to OpenAI-compatible messages format.

        Args:
            include_chunks: Whether to include raw streaming chunks in output

        Returns:
            Dictionary in OpenAI chat completion format with extended metadata
        """
        result = {
            "id": self.call_id,
            "object": "chat.completion",
            "created": int(self.start_time),
            "model": self.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": self.output_content or None,
                    },
                    "finish_reason": self.finish_reason,
                },
            ],
            "usage": {
                "prompt_tokens": self.input_tokens,
                "completion_tokens": self.output_tokens,
                "total_tokens": self.input_tokens + self.output_tokens,
            },
            # Extended metadata
            "_massgen": {
                "agent_id": self.agent_id,
                "backend_name": self.backend_name,
                "input_messages": self.messages,
                "tools": self.tools,
                "timing": {
                    "start": self.start_time,
                    "first_chunk": self.first_chunk_time,
                    "end": self.end_time,
                    "duration_seconds": self.end_time - self.start_time if self.end_time else 0,
                    "time_to_first_chunk": (self.first_chunk_time - self.start_time if self.first_chunk_time else 0),
                },
                "chunk_count": self.chunk_count,
            },
        }

        # Add tool_calls if present
        if self.output_tool_calls:
            result["choices"][0]["message"]["tool_calls"] = self.output_tool_calls

        # Add reasoning if present (non-standard but useful for analysis)
        if self.output_reasoning:
            result["choices"][0]["message"]["_reasoning"] = self.output_reasoning

        # Include raw chunks if requested
        if include_chunks and self.chunks:
            result["_massgen"]["chunks"] = self.chunks

        return result


class LLMCallLogger:
    """Manages logging of all LLM calls during a session.

    This logger tracks every LLM API call and saves them as JSON files
    in OpenAI's chat completion format, with extended metadata for debugging.

    Example:
        logger = LLMCallLogger(enabled=True, save_chunks=True)
        set_llm_call_logger(logger)

        # Then in backend code:
        call_id = get_llm_call_logger().start_call(...)
        # ... streaming ...
        get_llm_call_logger().end_call(call_id, ...)
    """

    def __init__(self, enabled: bool = False, save_chunks: bool = False):
        """Initialize the LLM call logger.

        Args:
            enabled: Whether logging is enabled
            save_chunks: Whether to save individual streaming chunks
        """
        self.enabled = enabled
        self.save_chunks = save_chunks
        self._call_counter: Dict[str, int] = {}  # agent_id -> call count
        self._active_calls: Dict[str, LLMCallRecord] = {}  # call_id -> record

    def start_call(
        self,
        agent_id: str,
        backend_name: str,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Start tracking a new LLM call.

        Args:
            agent_id: ID of the agent making the call
            backend_name: Name of the backend provider
            model: Model being used
            messages: Input messages sent to the LLM
            tools: Tools/functions available to the LLM

        Returns:
            call_id: Unique identifier for this call (empty string if logging disabled)
        """
        if not self.enabled:
            return ""

        # Generate call_id
        self._call_counter.setdefault(agent_id, 0)
        self._call_counter[agent_id] += 1
        call_num = self._call_counter[agent_id]
        call_id = f"{agent_id}_call_{call_num:03d}"

        record = LLMCallRecord(
            call_id=call_id,
            agent_id=agent_id,
            backend_name=backend_name,
            model=model,
            messages=messages,
            tools=tools or [],
            start_time=time.time(),
        )

        self._active_calls[call_id] = record
        logger.debug(f"[LLMCallLogger] Started call {call_id} for {agent_id}")

        return call_id

    def record_chunk(
        self,
        call_id: str,
        chunk_type: str,
        content: Optional[Any] = None,
        tool_calls: Optional[List[Dict]] = None,
        reasoning: Optional[str] = None,
        finish_reason: Optional[str] = None,
    ) -> None:
        """Record a streaming chunk.

        Args:
            call_id: ID from start_call()
            chunk_type: Type of chunk (content, tool_calls, reasoning, done, etc.)
            content: Text content for content chunks
            tool_calls: Tool call data for tool_calls chunks
            reasoning: Reasoning/thinking content
            finish_reason: Finish reason (stop, tool_calls, etc.)
        """
        if not self.enabled or call_id not in self._active_calls:
            return

        record = self._active_calls[call_id]
        record.chunk_count += 1

        # Record first chunk time
        if record.first_chunk_time == 0.0:
            record.first_chunk_time = time.time()

        # Accumulate content based on chunk type
        if chunk_type == "content" and content:
            record.output_content += str(content)
        elif chunk_type == "tool_calls" and tool_calls:
            record.output_tool_calls.extend(tool_calls)
        elif chunk_type == "reasoning" and reasoning:
            record.output_reasoning += str(reasoning)

        if finish_reason:
            record.finish_reason = finish_reason

        # Optionally save raw chunks
        if self.save_chunks:
            record.chunks.append(
                {
                    "time": time.time(),
                    "type": chunk_type,
                    "content": content,
                    "tool_calls": tool_calls,
                    "reasoning": reasoning,
                    "finish_reason": finish_reason,
                },
            )

    def end_call(
        self,
        call_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        finish_reason: Optional[str] = None,
    ) -> None:
        """End tracking and save the call record.

        Args:
            call_id: ID from start_call()
            input_tokens: Number of input/prompt tokens
            output_tokens: Number of output/completion tokens
            finish_reason: Final finish reason if not already set
        """
        if not self.enabled or call_id not in self._active_calls:
            return

        record = self._active_calls[call_id]
        record.end_time = time.time()
        record.input_tokens = input_tokens
        record.output_tokens = output_tokens

        if finish_reason and not record.finish_reason:
            record.finish_reason = finish_reason

        # Save to file
        self._save_record(record)

        # Clean up
        del self._active_calls[call_id]

        duration = record.end_time - record.start_time
        logger.debug(
            f"[LLMCallLogger] Ended call {call_id}: " f"{record.chunk_count} chunks, {duration:.2f}s, " f"{input_tokens}+{output_tokens} tokens",
        )

    def _save_record(self, record: LLMCallRecord) -> None:
        """Save record to JSON file.

        Args:
            record: The LLM call record to save
        """
        # Import here to avoid circular imports
        from .logger_config import get_log_session_dir

        log_dir = get_log_session_dir()
        llm_calls_dir = log_dir / "llm_calls"
        llm_calls_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{record.call_id}.json"
        filepath = llm_calls_dir / filename

        try:
            with open(filepath, "w") as f:
                json.dump(
                    record.to_openai_format(include_chunks=self.save_chunks),
                    f,
                    indent=2,
                    default=str,
                )
            logger.debug(f"[LLMCallLogger] Saved {filepath}")
        except Exception as e:
            logger.warning(f"[LLMCallLogger] Failed to save {filepath}: {e}")

    def get_call_count(self, agent_id: Optional[str] = None) -> int:
        """Get the number of calls made.

        Args:
            agent_id: If provided, return count for specific agent

        Returns:
            Total call count or count for specific agent
        """
        if agent_id:
            return self._call_counter.get(agent_id, 0)
        return sum(self._call_counter.values())


# Global instance (set by CLI)
_llm_call_logger: Optional[LLMCallLogger] = None


def get_llm_call_logger() -> Optional[LLMCallLogger]:
    """Get the global LLM call logger instance.

    Returns:
        The logger instance, or None if not configured
    """
    return _llm_call_logger


def set_llm_call_logger(llm_logger: LLMCallLogger) -> None:
    """Set the global LLM call logger instance.

    Args:
        llm_logger: The logger instance to use globally
    """
    global _llm_call_logger
    _llm_call_logger = llm_logger
    if llm_logger and llm_logger.enabled:
        logger.info(
            f"[LLMCallLogger] Enabled (save_chunks={llm_logger.save_chunks})",
        )
