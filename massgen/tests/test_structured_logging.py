# -*- coding: utf-8 -*-
"""
Tests for structured logging module.

These tests verify:
- TracerProxy graceful degradation when Logfire is disabled
- Configuration options work correctly
- Context managers and decorators function properly
"""

import pytest

from massgen.structured_logging import (
    ObservabilityConfig,
    TracerProxy,
    configure_observability,
    get_tracer,
    is_observability_enabled,
    log_coordination_event,
    log_token_usage,
    log_tool_execution,
    trace_agent_execution,
    trace_orchestrator_operation,
)


class TestTracerProxy:
    """Tests for TracerProxy graceful degradation."""

    def test_tracer_proxy_span_when_disabled(self):
        """TracerProxy.span() should work when Logfire is disabled."""
        tracer = TracerProxy()
        # Should not raise even when Logfire is disabled
        with tracer.span("test_span", attributes={"key": "value"}) as span:
            span.set_attribute("test", "value")
            span.record_exception(ValueError("test"))
            span.add_event("test_event", {"attr": "value"})

    def test_tracer_proxy_info_when_disabled(self):
        """TracerProxy.info() should fall back to loguru when Logfire is disabled."""
        tracer = TracerProxy()
        # Should not raise
        tracer.info("Test message", key="value")

    def test_tracer_proxy_debug_when_disabled(self):
        """TracerProxy.debug() should fall back to loguru when Logfire is disabled."""
        tracer = TracerProxy()
        tracer.debug("Test debug message", key="value")

    def test_tracer_proxy_warning_when_disabled(self):
        """TracerProxy.warning() should fall back to loguru when Logfire is disabled."""
        tracer = TracerProxy()
        tracer.warning("Test warning message", key="value")

    def test_tracer_proxy_error_when_disabled(self):
        """TracerProxy.error() should fall back to loguru when Logfire is disabled."""
        tracer = TracerProxy()
        tracer.error("Test error message", key="value")

    def test_instrument_methods_graceful_when_disabled(self):
        """Instrumentation methods should not raise when Logfire is disabled."""
        tracer = TracerProxy()
        # These should not raise even when Logfire is not configured
        tracer.instrument_openai(None)
        tracer.instrument_anthropic(None)
        tracer.instrument_aiohttp()


class TestConfiguration:
    """Tests for observability configuration."""

    def test_configure_observability_disabled_by_default(self):
        """Observability should be disabled when enabled=False."""
        result = configure_observability(enabled=False)
        assert result is False
        assert is_observability_enabled() is False

    def test_configure_observability_with_env_var(self, monkeypatch):
        """Observability should respect MASSGEN_LOGFIRE_ENABLED env var."""
        # Disabled by default
        monkeypatch.delenv("MASSGEN_LOGFIRE_ENABLED", raising=False)
        result = configure_observability(enabled=None)
        assert result is False

    def test_get_tracer_returns_singleton(self):
        """get_tracer() should return the same instance."""
        tracer1 = get_tracer()
        tracer2 = get_tracer()
        assert tracer1 is tracer2

    def test_observability_config_defaults(self):
        """ObservabilityConfig should have sensible defaults."""
        config = ObservabilityConfig()
        assert config.enabled is False
        assert config.service_name == "massgen"
        assert config.environment == "development"
        assert config.send_to_logfire is True
        assert config.scrub_sensitive_data is True


class TestContextManagers:
    """Tests for tracing context managers."""

    def test_trace_orchestrator_operation(self):
        """trace_orchestrator_operation should work without errors."""
        with trace_orchestrator_operation(
            "test_operation",
            task="Test task",
            num_agents=3,
        ) as span:
            # Should be able to access span
            assert span is not None

    def test_trace_agent_execution(self):
        """trace_agent_execution should work without errors."""
        with trace_agent_execution(
            agent_id="agent_1",
            backend_name="openai",
            model="gpt-4",
            round_number=1,
            round_type="coordination",
        ) as span:
            assert span is not None


class TestEventLoggers:
    """Tests for structured event logging functions."""

    def test_log_token_usage(self):
        """log_token_usage should not raise."""
        # Should not raise
        log_token_usage(
            agent_id="agent_1",
            input_tokens=100,
            output_tokens=50,
            reasoning_tokens=10,
            cached_tokens=5,
            estimated_cost=0.001,
            model="gpt-4",
        )

    def test_log_tool_execution_success(self):
        """log_tool_execution should handle success case."""
        log_tool_execution(
            agent_id="agent_1",
            tool_name="mcp__server__tool",
            tool_type="mcp",
            execution_time_ms=150.5,
            success=True,
            input_chars=100,
            output_chars=200,
        )

    def test_log_tool_execution_failure(self):
        """log_tool_execution should handle failure case."""
        log_tool_execution(
            agent_id="agent_1",
            tool_name="mcp__server__tool",
            tool_type="mcp",
            execution_time_ms=50.0,
            success=False,
            error_message="Tool execution failed",
        )

    def test_log_coordination_event(self):
        """log_coordination_event should not raise."""
        log_coordination_event(
            event_type="winner_selected",
            agent_id="agent_1",
            details={"turn": 1, "vote_count": 3},
        )

    def test_log_coordination_event_minimal(self):
        """log_coordination_event should work with minimal args."""
        log_coordination_event(event_type="coordination_started")


class TestDecorators:
    """Tests for tracing decorators."""

    def test_trace_llm_call_decorator_sync(self):
        """trace_llm_call decorator should work with sync functions."""
        from massgen.structured_logging import trace_llm_call

        @trace_llm_call(backend_name="openai", model="gpt-4")
        def sync_function():
            return "result"

        result = sync_function()
        assert result == "result"

    @pytest.mark.asyncio
    async def test_trace_llm_call_decorator_async(self):
        """trace_llm_call decorator should work with async functions."""
        from massgen.structured_logging import trace_llm_call

        @trace_llm_call(backend_name="anthropic", model="claude-3")
        async def async_function():
            return "async_result"

        result = await async_function()
        assert result == "async_result"

    def test_trace_tool_call_decorator_sync(self):
        """trace_tool_call decorator should work with sync functions."""
        from massgen.structured_logging import trace_tool_call

        @trace_tool_call(tool_name="test_tool", tool_type="custom")
        def sync_tool():
            return {"success": True}

        result = sync_tool()
        assert result == {"success": True}

    @pytest.mark.asyncio
    async def test_trace_tool_call_decorator_async(self):
        """trace_tool_call decorator should work with async functions."""
        from massgen.structured_logging import trace_tool_call

        @trace_tool_call(tool_name="async_tool", tool_type="mcp")
        async def async_tool():
            return {"success": True}

        result = await async_tool()
        assert result == {"success": True}

    def test_trace_tool_call_handles_exceptions(self):
        """trace_tool_call should record exceptions properly."""
        from massgen.structured_logging import trace_tool_call

        @trace_tool_call(tool_name="failing_tool", tool_type="custom")
        def failing_tool():
            raise ValueError("Tool failed")

        with pytest.raises(ValueError, match="Tool failed"):
            failing_tool()


class TestCoordinationTracing:
    """Tests for coordination-specific tracing functions."""

    def test_trace_coordination_session(self):
        """trace_coordination_session context manager should work."""
        from massgen.structured_logging import trace_coordination_session

        with trace_coordination_session(
            task="Test task",
            num_agents=3,
            agent_ids=["agent_a", "agent_b", "agent_c"],
        ) as span:
            assert span is not None

    def test_trace_coordination_iteration(self):
        """trace_coordination_iteration context manager should work."""
        from massgen.structured_logging import trace_coordination_iteration

        with trace_coordination_iteration(
            iteration=1,
            available_answers=["agent1.1", "agent2.1"],
        ) as span:
            assert span is not None

    def test_trace_agent_round(self):
        """trace_agent_round context manager should work."""
        from massgen.structured_logging import trace_agent_round

        with trace_agent_round(
            agent_id="agent_a",
            iteration=1,
            round_type="coordination",
            context_labels=["agent1.1"],
        ) as span:
            assert span is not None

    def test_log_agent_answer(self):
        """log_agent_answer should not raise."""
        from massgen.structured_logging import log_agent_answer

        log_agent_answer(
            agent_id="agent_a",
            answer_label="agent1.1",
            iteration=1,
            round_number=1,
            answer_preview="This is a test answer...",
        )

    def test_log_agent_vote(self):
        """log_agent_vote should not raise."""
        from massgen.structured_logging import log_agent_vote

        log_agent_vote(
            agent_id="agent_b",
            voted_for_label="agent1.1",
            iteration=1,
            round_number=1,
            reason="Better solution",
            available_answers=["agent1.1", "agent2.1"],
        )

    def test_log_winner_selected(self):
        """log_winner_selected should not raise."""
        from massgen.structured_logging import log_winner_selected

        log_winner_selected(
            winner_agent_id="agent_a",
            winner_label="agent1.1",
            vote_counts={"agent1.1": 2, "agent2.1": 1},
            total_iterations=3,
        )

    def test_log_final_answer(self):
        """log_final_answer should not raise."""
        from massgen.structured_logging import log_final_answer

        log_final_answer(
            agent_id="agent_a",
            iteration=3,
            answer_preview="This is the final answer...",
        )

    def test_log_iteration_end(self):
        """log_iteration_end should not raise."""
        from massgen.structured_logging import log_iteration_end

        log_iteration_end(
            iteration=1,
            end_reason="all_voted",
            votes_cast=3,
            answers_provided=2,
        )

    def test_nested_coordination_spans(self):
        """Nested coordination spans should work correctly."""
        from massgen.structured_logging import (
            log_agent_answer,
            log_agent_vote,
            trace_coordination_iteration,
            trace_coordination_session,
        )

        with trace_coordination_session(
            task="Nested test",
            num_agents=2,
            agent_ids=["agent_a", "agent_b"],
        ):
            with trace_coordination_iteration(iteration=1):
                log_agent_answer(
                    agent_id="agent_a",
                    answer_label="agent1.1",
                    iteration=1,
                    round_number=1,
                )
                log_agent_vote(
                    agent_id="agent_b",
                    voted_for_label="agent1.1",
                    iteration=1,
                    round_number=1,
                )
            with trace_coordination_iteration(iteration=2):
                log_agent_vote(
                    agent_id="agent_a",
                    voted_for_label="agent1.1",
                    iteration=2,
                    round_number=1,
                )


class TestLLMAPICallTracing:
    """Tests for LLM API call tracing with agent attribution."""

    def test_trace_llm_api_call_basic(self):
        """trace_llm_api_call should work as a context manager."""
        from massgen.structured_logging import trace_llm_api_call

        with trace_llm_api_call(
            agent_id="agent_1",
            provider="anthropic",
            model="claude-3-opus",
            operation="stream",
        ):
            # Simulate API call
            pass

    def test_trace_llm_api_call_with_extra_attributes(self):
        """trace_llm_api_call should accept extra attributes."""
        from massgen.structured_logging import trace_llm_api_call

        with trace_llm_api_call(
            agent_id="agent_2",
            provider="openai",
            model="gpt-4o",
            operation="create",
            request_id="test-123",
            max_tokens=1000,
        ):
            pass

    def test_trace_llm_api_call_yields_span(self):
        """trace_llm_api_call should yield a span object."""
        from massgen.structured_logging import trace_llm_api_call

        with trace_llm_api_call(
            agent_id="agent_3",
            provider="gemini",
            model="gemini-pro",
        ) as span:
            # Span should be a valid object (or NoOpSpan)
            assert span is not None

    def test_trace_llm_api_call_handles_exceptions(self):
        """trace_llm_api_call should properly handle exceptions."""
        from massgen.structured_logging import trace_llm_api_call

        try:
            with trace_llm_api_call(
                agent_id="agent_4",
                provider="anthropic",
                model="claude-3-sonnet",
            ):
                raise ValueError("Test error")
        except ValueError:
            pass  # Expected
