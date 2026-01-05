# -*- coding: utf-8 -*-
"""
Unit tests for the general hook framework.

Tests:
- HookEvent and HookResult dataclasses
- PatternHook matching
- PythonCallableHook execution
- ExternalCommandHook execution
- GeneralHookManager registration and execution
- Built-in hooks (MidStreamInjection, ReminderExtraction)
"""

import json
from datetime import datetime

import pytest

from massgen.mcp_tools.hooks import (
    GeneralHookManager,
    HookEvent,
    HookResult,
    HookType,
    MidStreamInjectionHook,
    PatternHook,
    PythonCallableHook,
    ReminderExtractionHook,
)

# =============================================================================
# HookEvent Tests
# =============================================================================


class TestHookEvent:
    """Tests for HookEvent dataclass."""

    def test_basic_creation(self):
        """Test basic HookEvent creation."""
        event = HookEvent(
            hook_type="PreToolUse",
            session_id="session-123",
            orchestrator_id="orch-456",
            agent_id="agent-1",
            timestamp=datetime.utcnow(),
            tool_name="my_tool",
            tool_input={"arg1": "value1"},
        )
        assert event.hook_type == "PreToolUse"
        assert event.tool_name == "my_tool"
        assert event.tool_input == {"arg1": "value1"}
        assert event.tool_output is None

    def test_post_tool_use_with_output(self):
        """Test PostToolUse event with tool output."""
        event = HookEvent(
            hook_type="PostToolUse",
            session_id="session-123",
            orchestrator_id="orch-456",
            agent_id="agent-1",
            timestamp=datetime.utcnow(),
            tool_name="my_tool",
            tool_input={"arg1": "value1"},
            tool_output="Tool result here",
        )
        assert event.tool_output == "Tool result here"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = datetime.utcnow()
        event = HookEvent(
            hook_type="PreToolUse",
            session_id="s123",
            orchestrator_id="o456",
            agent_id="a1",
            timestamp=now,
            tool_name="test",
            tool_input={"key": "val"},
        )
        d = event.to_dict()
        assert d["hook_type"] == "PreToolUse"
        assert d["timestamp"] == now.isoformat()
        assert d["tool_input"] == {"key": "val"}

    def test_to_json(self):
        """Test JSON serialization."""
        event = HookEvent(
            hook_type="PreToolUse",
            session_id="s123",
            orchestrator_id="o456",
            agent_id="a1",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            tool_name="test",
            tool_input={},
        )
        j = event.to_json()
        parsed = json.loads(j)
        assert parsed["tool_name"] == "test"


# =============================================================================
# HookResult Tests
# =============================================================================


class TestHookResult:
    """Tests for HookResult dataclass."""

    def test_default_values(self):
        """Test default HookResult values."""
        result = HookResult()
        assert result.allowed is True
        assert result.decision == "allow"
        assert result.inject is None

    def test_deny_result(self):
        """Test deny result creation."""
        result = HookResult.deny(reason="Permission denied")
        assert result.allowed is False
        assert result.decision == "deny"
        assert result.reason == "Permission denied"

    def test_ask_result(self):
        """Test ask result creation."""
        result = HookResult.ask(reason="Need confirmation")
        assert result.allowed is True  # Still allowed until user denies
        assert result.decision == "ask"
        assert result.reason == "Need confirmation"

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "allowed": True,
            "decision": "allow",
            "inject": {"content": "injected", "strategy": "tool_result"},
        }
        result = HookResult.from_dict(data)
        assert result.inject == {"content": "injected", "strategy": "tool_result"}

    def test_sync_decision_allowed(self):
        """Test that allowed syncs with decision."""
        result = HookResult(allowed=False)
        assert result.decision == "deny"

    def test_sync_allowed_decision(self):
        """Test that decision syncs with allowed."""
        result = HookResult(decision="deny")
        assert result.allowed is False


# =============================================================================
# PatternHook Tests
# =============================================================================


class TestPatternHook:
    """Tests for pattern matching in hooks."""

    def test_wildcard_match(self):
        """Test wildcard pattern matching."""

        class TestHook(PatternHook):
            async def execute(self, *args, **kwargs):
                return HookResult.allow()

        hook = TestHook("test", matcher="*")
        assert hook.matches("any_tool_name")
        assert hook.matches("another_tool")

    def test_exact_match(self):
        """Test exact pattern matching."""

        class TestHook(PatternHook):
            async def execute(self, *args, **kwargs):
                return HookResult.allow()

        hook = TestHook("test", matcher="specific_tool")
        assert hook.matches("specific_tool")
        assert not hook.matches("other_tool")

    def test_prefix_match(self):
        """Test prefix pattern matching with *."""

        class TestHook(PatternHook):
            async def execute(self, *args, **kwargs):
                return HookResult.allow()

        hook = TestHook("test", matcher="mcp__*")
        assert hook.matches("mcp__read_file")
        assert hook.matches("mcp__write_file")
        assert not hook.matches("custom_read_file")

    def test_or_pattern(self):
        """Test OR pattern matching with |."""

        class TestHook(PatternHook):
            async def execute(self, *args, **kwargs):
                return HookResult.allow()

        hook = TestHook("test", matcher="read_file|write_file|execute_command")
        assert hook.matches("read_file")
        assert hook.matches("write_file")
        assert hook.matches("execute_command")
        assert not hook.matches("delete_file")


# =============================================================================
# PythonCallableHook Tests
# =============================================================================


class TestPythonCallableHook:
    """Tests for Python callable hooks."""

    @pytest.mark.asyncio
    async def test_sync_callable(self):
        """Test with a sync callable."""

        def my_hook(event: HookEvent) -> HookResult:
            return HookResult.allow()

        hook = PythonCallableHook("test", my_hook)
        result = await hook.execute("tool_name", "{}")
        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_async_callable(self):
        """Test with an async callable."""

        async def my_hook(event: HookEvent) -> HookResult:
            return HookResult.deny(reason="Test deny")

        hook = PythonCallableHook("test", my_hook)
        result = await hook.execute("tool_name", "{}")
        assert result.allowed is False
        assert result.reason == "Test deny"

    @pytest.mark.asyncio
    async def test_callable_returning_dict(self):
        """Test with a callable returning dict."""

        def my_hook(event: HookEvent) -> dict:
            return {"allowed": True, "inject": {"content": "test"}}

        hook = PythonCallableHook("test", my_hook)
        result = await hook.execute("tool_name", "{}")
        assert result.inject == {"content": "test"}

    @pytest.mark.asyncio
    async def test_pattern_non_match_returns_allow(self):
        """Test that non-matching patterns return allow."""

        def my_hook(event: HookEvent) -> HookResult:
            return HookResult.deny()

        hook = PythonCallableHook("test", my_hook, matcher="specific_tool")
        result = await hook.execute("other_tool", "{}")
        assert result.allowed is True  # Non-match returns allow

    @pytest.mark.asyncio
    async def test_modified_arguments(self):
        """Test hook that modifies arguments."""

        def my_hook(event: HookEvent) -> HookResult:
            return HookResult(
                allowed=True,
                updated_input={"modified": True},
            )

        hook = PythonCallableHook("test", my_hook)
        result = await hook.execute("tool_name", '{"original": true}')
        assert result.updated_input == {"modified": True}


# =============================================================================
# GeneralHookManager Tests
# =============================================================================


class TestGeneralHookManager:
    """Tests for GeneralHookManager."""

    def test_register_global_hook(self):
        """Test global hook registration."""
        manager = GeneralHookManager()

        def my_hook(event):
            return HookResult.allow()

        hook = PythonCallableHook("test", my_hook)
        manager.register_global_hook(HookType.PRE_TOOL_USE, hook)

        hooks = manager.get_hooks_for_agent(None, HookType.PRE_TOOL_USE)
        assert len(hooks) == 1
        assert hooks[0].name == "test"

    def test_register_agent_hook(self):
        """Test agent-specific hook registration."""
        manager = GeneralHookManager()

        def my_hook(event):
            return HookResult.allow()

        hook = PythonCallableHook("test", my_hook)
        manager.register_agent_hook("agent-1", HookType.PRE_TOOL_USE, hook)

        # Agent-1 gets the hook
        hooks = manager.get_hooks_for_agent("agent-1", HookType.PRE_TOOL_USE)
        assert len(hooks) == 1

        # Other agents don't
        hooks = manager.get_hooks_for_agent("agent-2", HookType.PRE_TOOL_USE)
        assert len(hooks) == 0

    def test_agent_override(self):
        """Test agent override disables global hooks."""
        manager = GeneralHookManager()

        def global_hook(event):
            return HookResult.allow()

        def agent_hook(event):
            return HookResult.allow()

        g_hook = PythonCallableHook("global", global_hook)
        a_hook = PythonCallableHook("agent", agent_hook)

        manager.register_global_hook(HookType.PRE_TOOL_USE, g_hook)
        manager.register_agent_hook(
            "agent-1",
            HookType.PRE_TOOL_USE,
            a_hook,
            override=True,
        )

        # Agent-1 only gets agent hook (override)
        hooks = manager.get_hooks_for_agent("agent-1", HookType.PRE_TOOL_USE)
        assert len(hooks) == 1
        assert hooks[0].name == "agent"

        # Other agents get global hook
        hooks = manager.get_hooks_for_agent("agent-2", HookType.PRE_TOOL_USE)
        assert len(hooks) == 1
        assert hooks[0].name == "global"

    @pytest.mark.asyncio
    async def test_execute_hooks_deny_short_circuits(self):
        """Test that deny result short-circuits hook execution."""
        manager = GeneralHookManager()

        def deny_hook(event):
            return HookResult.deny(reason="Denied!")

        def allow_hook(event):
            return HookResult.allow()

        manager.register_global_hook(
            HookType.PRE_TOOL_USE,
            PythonCallableHook("deny", deny_hook),
        )
        manager.register_global_hook(
            HookType.PRE_TOOL_USE,
            PythonCallableHook("allow", allow_hook),
        )

        result = await manager.execute_hooks(
            HookType.PRE_TOOL_USE,
            "tool",
            "{}",
            {},
        )
        assert result.decision == "deny"
        assert "Denied!" in result.reason

    @pytest.mark.asyncio
    async def test_execute_hooks_aggregates_injections(self):
        """Test that PostToolUse hooks aggregate injection content."""
        manager = GeneralHookManager()

        def hook1(event):
            return HookResult(inject={"content": "First", "strategy": "tool_result"})

        def hook2(event):
            return HookResult(inject={"content": "Second", "strategy": "tool_result"})

        manager.register_global_hook(
            HookType.POST_TOOL_USE,
            PythonCallableHook("h1", hook1),
        )
        manager.register_global_hook(
            HookType.POST_TOOL_USE,
            PythonCallableHook("h2", hook2),
        )

        result = await manager.execute_hooks(
            HookType.POST_TOOL_USE,
            "tool",
            "{}",
            {},
            tool_output="output",
        )
        assert "First" in result.inject["content"]
        assert "Second" in result.inject["content"]

    def test_register_hooks_from_config(self):
        """Test configuration-based hook registration."""
        manager = GeneralHookManager()

        config = {
            "PreToolUse": [
                {"handler": "massgen.mcp_tools.hooks.HookResult.allow", "matcher": "*"},
            ],
            "PostToolUse": [
                {"handler": "massgen.mcp_tools.hooks.HookResult.allow", "matcher": "*"},
            ],
        }

        manager.register_hooks_from_config(config)

        pre_hooks = manager.get_hooks_for_agent(None, HookType.PRE_TOOL_USE)
        post_hooks = manager.get_hooks_for_agent(None, HookType.POST_TOOL_USE)
        assert len(pre_hooks) == 1
        assert len(post_hooks) == 1


# =============================================================================
# Built-in Hook Tests
# =============================================================================


class TestMidStreamInjectionHook:
    """Tests for MidStreamInjectionHook."""

    @pytest.mark.asyncio
    async def test_no_callback_returns_allow(self):
        """Test hook without callback returns allow."""
        hook = MidStreamInjectionHook()
        result = await hook.execute("tool", "{}")
        assert result.allowed is True
        assert result.inject is None

    @pytest.mark.asyncio
    async def test_callback_returns_none(self):
        """Test hook with callback returning None."""
        hook = MidStreamInjectionHook()
        hook.set_callback(lambda: None)
        result = await hook.execute("tool", "{}")
        assert result.inject is None

    @pytest.mark.asyncio
    async def test_callback_returns_content(self):
        """Test hook with callback returning content."""
        hook = MidStreamInjectionHook()
        hook.set_callback(lambda: "Injected content from other agent")
        result = await hook.execute("tool", "{}")
        assert result.inject is not None
        assert result.inject["content"] == "Injected content from other agent"
        assert result.inject["strategy"] == "tool_result"


class TestReminderExtractionHook:
    """Tests for ReminderExtractionHook."""

    @pytest.mark.asyncio
    async def test_no_output_returns_allow(self):
        """Test hook without tool output returns allow."""
        hook = ReminderExtractionHook()
        result = await hook.execute("tool", "{}", {})
        assert result.allowed is True
        assert result.inject is None

    @pytest.mark.asyncio
    async def test_non_json_output_returns_allow(self):
        """Test hook with non-JSON output returns allow."""
        hook = ReminderExtractionHook()
        result = await hook.execute(
            "tool",
            "{}",
            {"tool_output": "plain text output"},
        )
        assert result.inject is None

    @pytest.mark.asyncio
    async def test_json_without_reminder_returns_allow(self):
        """Test hook with JSON lacking reminder field returns allow."""
        hook = ReminderExtractionHook()
        result = await hook.execute(
            "tool",
            "{}",
            {"tool_output": '{"result": "success"}'},
        )
        assert result.inject is None

    @pytest.mark.asyncio
    async def test_json_with_reminder_extracts_it(self):
        """Test hook extracts reminder from JSON output."""
        hook = ReminderExtractionHook()
        result = await hook.execute(
            "tool",
            "{}",
            {"tool_output": '{"result": "ok", "reminder": "Remember this!"}'},
        )
        assert result.inject is not None
        assert result.inject["content"] == "Remember this!"
        assert result.inject["strategy"] == "user_message"
