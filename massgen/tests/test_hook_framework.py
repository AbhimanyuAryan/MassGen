# -*- coding: utf-8 -*-
"""
Unit tests for the general hook framework.

Tests:
- HookEvent and HookResult dataclasses
- PatternHook matching
- PythonCallableHook execution
- GeneralHookManager registration and execution
- Built-in hooks (MidStreamInjection, HighPriorityTaskReminder)
"""

import json
from datetime import datetime

import pytest

from massgen.mcp_tools.hooks import (
    GeneralHookManager,
    HighPriorityTaskReminderHook,
    HookEvent,
    HookResult,
    HookType,
    MidStreamInjectionHook,
    PatternHook,
    PythonCallableHook,
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

    @pytest.mark.asyncio
    async def test_fail_open_on_error_by_default(self):
        """Test that hooks fail open (allow) on errors by default."""

        def failing_hook(event: HookEvent) -> HookResult:
            raise RuntimeError("Hook crashed!")

        hook = PythonCallableHook("test", failing_hook)
        result = await hook.execute("tool_name", "{}")
        # Default is fail-open: allow execution despite error
        assert result.allowed is True
        assert result.decision == "allow"

    @pytest.mark.asyncio
    async def test_fail_closed_on_error_when_configured(self):
        """Test that hooks fail closed (deny) on errors when fail_closed=True."""

        def failing_hook(event: HookEvent) -> HookResult:
            raise RuntimeError("Hook crashed!")

        hook = PythonCallableHook("test", failing_hook, fail_closed=True)
        result = await hook.execute("tool_name", "{}")
        # fail_closed=True: deny execution on error
        assert result.allowed is False
        assert result.decision == "deny"
        assert "failed" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_fail_closed_on_timeout(self):
        """Test that hooks fail closed on timeout when fail_closed=True."""
        import asyncio

        async def slow_hook(event: HookEvent) -> HookResult:
            await asyncio.sleep(10)  # Will timeout
            return HookResult.allow()

        # Very short timeout to trigger timeout error
        hook = PythonCallableHook("test", slow_hook, timeout=0.01, fail_closed=True)
        result = await hook.execute("tool_name", "{}")
        assert result.allowed is False
        assert result.decision == "deny"
        assert "timed out" in result.reason.lower()


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

    @pytest.mark.asyncio
    async def test_deny_with_pattern_only_blocks_matching_tools(self):
        """Test that deny hook with pattern only blocks matching tools."""
        manager = GeneralHookManager()

        def deny_dangerous_tools(event):
            return HookResult.deny(reason="Dangerous tool blocked")

        # Register deny hook only for Write and Delete tools
        manager.register_global_hook(
            HookType.PRE_TOOL_USE,
            PythonCallableHook("block_writes", deny_dangerous_tools, matcher="Write|Delete"),
        )

        # Write tool should be blocked
        result = await manager.execute_hooks(
            HookType.PRE_TOOL_USE,
            "Write",
            '{"file": "test.txt"}',
            {},
        )
        assert result.decision == "deny"
        assert result.allowed is False
        assert "Dangerous tool blocked" in result.reason

        # Delete tool should be blocked
        result = await manager.execute_hooks(
            HookType.PRE_TOOL_USE,
            "Delete",
            '{"file": "test.txt"}',
            {},
        )
        assert result.decision == "deny"
        assert result.allowed is False

        # Read tool should be allowed (doesn't match pattern)
        result = await manager.execute_hooks(
            HookType.PRE_TOOL_USE,
            "Read",
            '{"file": "test.txt"}',
            {},
        )
        assert result.decision == "allow"
        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_deny_propagates_reason_correctly(self):
        """Test that deny reason is properly propagated through hook execution."""
        manager = GeneralHookManager()

        custom_reason = "Access denied: insufficient permissions for /etc/passwd"

        def security_check(event):
            # Check if trying to access sensitive files
            tool_input = event.tool_input
            if tool_input.get("file_path", "").startswith("/etc/"):
                return HookResult.deny(reason=custom_reason)
            return HookResult.allow()

        manager.register_global_hook(
            HookType.PRE_TOOL_USE,
            PythonCallableHook("security", security_check, matcher="*"),
        )

        # Access to /etc should be denied with specific reason
        result = await manager.execute_hooks(
            HookType.PRE_TOOL_USE,
            "Read",
            '{"file_path": "/etc/passwd"}',
            {},
        )
        assert result.decision == "deny"
        assert result.reason == custom_reason

        # Access to /home should be allowed
        result = await manager.execute_hooks(
            HookType.PRE_TOOL_USE,
            "Read",
            '{"file_path": "/home/user/file.txt"}',
            {},
        )
        assert result.decision == "allow"


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


class TestHighPriorityTaskReminderHook:
    """Tests for HighPriorityTaskReminderHook."""

    @pytest.mark.asyncio
    async def test_no_output_returns_allow(self):
        """Test hook without tool output returns allow."""
        hook = HighPriorityTaskReminderHook()
        result = await hook.execute("mcp__planning__update_task_status", "{}", {})
        assert result.allowed is True
        assert result.inject is None

    @pytest.mark.asyncio
    async def test_non_matching_tool_returns_allow(self):
        """Test hook with non-matching tool name returns allow without checking output."""
        hook = HighPriorityTaskReminderHook()
        # Even with valid high-priority task output, should not inject for wrong tool
        tool_output = json.dumps(
            {
                "task": {"priority": "high", "status": "completed"},
                "newly_ready_tasks": [],
            },
        )
        result = await hook.execute(
            "other_tool",
            "{}",
            {"tool_output": tool_output},
        )
        assert result.inject is None

    @pytest.mark.asyncio
    async def test_non_json_output_returns_allow(self):
        """Test hook with non-JSON output returns allow."""
        hook = HighPriorityTaskReminderHook()
        result = await hook.execute(
            "mcp__planning__update_task_status",
            "{}",
            {"tool_output": "plain text output"},
        )
        assert result.inject is None

    @pytest.mark.asyncio
    async def test_low_priority_task_returns_allow(self):
        """Test hook with low-priority completed task returns allow."""
        hook = HighPriorityTaskReminderHook()
        tool_output = json.dumps(
            {
                "task": {"priority": "low", "status": "completed"},
                "newly_ready_tasks": [],
            },
        )
        result = await hook.execute(
            "mcp__planning__update_task_status",
            "{}",
            {"tool_output": tool_output},
        )
        assert result.inject is None

    @pytest.mark.asyncio
    async def test_high_priority_incomplete_task_returns_allow(self):
        """Test hook with high-priority but incomplete task returns allow."""
        hook = HighPriorityTaskReminderHook()
        tool_output = json.dumps(
            {
                "task": {"priority": "high", "status": "in_progress"},
                "newly_ready_tasks": [],
            },
        )
        result = await hook.execute(
            "mcp__planning__update_task_status",
            "{}",
            {"tool_output": tool_output},
        )
        assert result.inject is None

    @pytest.mark.asyncio
    async def test_high_priority_completed_task_injects_reminder(self):
        """Test hook injects reminder for high-priority completed task."""
        hook = HighPriorityTaskReminderHook()
        tool_output = json.dumps(
            {
                "task": {"priority": "high", "status": "completed"},
                "newly_ready_tasks": [],
            },
        )
        result = await hook.execute(
            "mcp__planning__update_task_status",
            "{}",
            {"tool_output": tool_output},
        )
        assert result.inject is not None
        # Reminder should be formatted with SYSTEM REMINDER header and borders
        assert "High-priority task completed" in result.inject["content"]
        assert "SYSTEM REMINDER" in result.inject["content"]
        assert "=" * 60 in result.inject["content"]  # Border separator
        assert "memory/long_term" in result.inject["content"]  # Memory paths
        assert result.inject["strategy"] == "user_message"
