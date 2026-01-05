# -*- coding: utf-8 -*-
"""
Hook system for MCP tool call interception.

This module provides the infrastructure for intercepting tool calls
across different backend architectures:

1. Function-based backends (OpenAI, Claude, etc.) - use FunctionHook
2. Session-based backends (Gemini) - use PermissionClientSession

Hook Types:
- PRE_TOOL_USE: Fires before tool execution (can block or modify)
- POST_TOOL_USE: Fires after tool execution (can inject content)

Hook Registration:
- Global hooks: Apply to all agents (top-level `hooks:` in config)
- Per-agent hooks: Apply to specific agents (in `backend.hooks:`)
- Per-agent hooks can extend or override global hooks

The actual permission logic is implemented in filesystem_manager.py
"""

import asyncio
import fnmatch
import importlib
import json
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, Union

from ..logger_config import logger

# MCP imports for session-based backends
try:
    from mcp import ClientSession, types
    from mcp.client.session import ProgressFnT

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    ClientSession = object
    types = None
    ProgressFnT = None


class HookType(Enum):
    """Types of function call hooks."""

    # Legacy hook types (for backward compatibility)
    PRE_CALL = "pre_call"
    POST_CALL = "post_call"

    # New general hook types
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"


@dataclass
class HookEvent:
    """Input data provided to all hooks.

    This dataclass represents the context passed to hook handlers,
    containing information about the tool call and agent state.
    """

    hook_type: str  # "PreToolUse" or "PostToolUse"
    session_id: str
    orchestrator_id: str
    agent_id: Optional[str]
    timestamp: datetime
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Optional[str] = None  # Only populated for PostToolUse

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "hook_type": self.hook_type,
            "session_id": self.session_id,
            "orchestrator_id": self.orchestrator_id,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "tool_output": self.tool_output,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class HookResult:
    """Result of a hook execution.

    This dataclass is backward compatible with the old HookResult class
    while adding new fields for the general hook framework.
    """

    # Legacy fields (for backward compatibility)
    allowed: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    modified_args: Optional[str] = None

    # New fields for general hook framework
    decision: Literal["allow", "deny", "ask"] = "allow"
    reason: Optional[str] = None
    updated_input: Optional[Dict[str, Any]] = None  # For PreToolUse
    inject: Optional[Dict[str, Any]] = None  # For PostToolUse injection

    def __post_init__(self):
        """Sync legacy and new fields for compatibility."""
        # Sync decision with allowed
        if not self.allowed:
            self.decision = "deny"
        elif self.decision == "deny":
            self.allowed = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HookResult":
        """Create HookResult from dictionary (e.g., from JSON)."""
        return cls(
            allowed=data.get("allowed", True),
            metadata=data.get("metadata", {}),
            modified_args=data.get("modified_args"),
            decision=data.get("decision", "allow"),
            reason=data.get("reason"),
            updated_input=data.get("updated_input"),
            inject=data.get("inject"),
        )

    @classmethod
    def allow(cls) -> "HookResult":
        """Create a result that allows the operation."""
        return cls(allowed=True, decision="allow")

    @classmethod
    def deny(cls, reason: Optional[str] = None) -> "HookResult":
        """Create a result that denies the operation."""
        return cls(allowed=False, decision="deny", reason=reason)

    @classmethod
    def ask(cls, reason: Optional[str] = None) -> "HookResult":
        """Create a result that requires user confirmation."""
        return cls(allowed=True, decision="ask", reason=reason)


class FunctionHook(ABC):
    """Base class for function call hooks."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def execute(self, function_name: str, arguments: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> HookResult:
        """
        Execute the hook.

        Args:
            function_name: Name of the function being called
            arguments: JSON string of arguments
            context: Additional context (backend, timestamp, etc.)

        Returns:
            HookResult with allowed flag and optional modifications
        """


class FunctionHookManager:
    """Manages registration and execution of function hooks."""

    def __init__(self):
        self._hooks: Dict[HookType, List[FunctionHook]] = {hook_type: [] for hook_type in HookType}
        self._global_hooks: Dict[HookType, List[FunctionHook]] = {hook_type: [] for hook_type in HookType}

    def register_hook(self, function_name: str, hook_type: HookType, hook: FunctionHook):
        """Register a hook for a specific function."""
        if function_name not in self._hooks:
            self._hooks[function_name] = {hook_type: [] for hook_type in HookType}

        if hook_type not in self._hooks[function_name]:
            self._hooks[function_name][hook_type] = []

        self._hooks[function_name][hook_type].append(hook)

    def register_global_hook(self, hook_type: HookType, hook: FunctionHook):
        """Register a hook that applies to all functions."""
        self._global_hooks[hook_type].append(hook)

    def get_hooks_for_function(self, function_name: str) -> Dict[HookType, List[FunctionHook]]:
        """Get all hooks (function-specific + global) for a function."""
        result = {hook_type: [] for hook_type in HookType}

        # Add global hooks first
        for hook_type in HookType:
            result[hook_type].extend(self._global_hooks[hook_type])

        # Add function-specific hooks
        if function_name in self._hooks:
            for hook_type in HookType:
                if hook_type in self._hooks[function_name]:
                    result[hook_type].extend(self._hooks[function_name][hook_type])

        return result

    def clear_hooks(self):
        """Clear all registered hooks."""
        self._hooks.clear()
        self._global_hooks = {hook_type: [] for hook_type in HookType}


# =============================================================================
# New General Hook Framework
# =============================================================================


class PatternHook(FunctionHook):
    """Base class for hooks that support pattern-based tool matching."""

    def __init__(
        self,
        name: str,
        matcher: str = "*",
        timeout: int = 30,
    ):
        """
        Initialize a pattern-based hook.

        Args:
            name: Hook identifier
            matcher: Glob pattern for tool name matching (e.g., "*", "Write|Edit", "mcp__*")
            timeout: Execution timeout in seconds
        """
        super().__init__(name)
        self.matcher = matcher
        self.timeout = timeout
        self._patterns = self._parse_matcher(matcher)

    def _parse_matcher(self, matcher: str) -> List[str]:
        """Parse matcher into list of patterns (supports | for OR)."""
        if not matcher:
            return ["*"]
        return [p.strip() for p in matcher.split("|") if p.strip()]

    def matches(self, tool_name: str) -> bool:
        """Check if this hook matches the given tool name."""
        for pattern in self._patterns:
            if fnmatch.fnmatch(tool_name, pattern):
                return True
        return False


class PythonCallableHook(PatternHook):
    """Hook that invokes a Python callable.

    The callable can be specified as:
    - A module path string (e.g., "massgen.hooks.my_hook")
    - A direct callable (function or async function)

    The callable receives a HookEvent and returns a HookResult (or dict).
    """

    def __init__(
        self,
        name: str,
        handler: Union[str, Callable],
        matcher: str = "*",
        timeout: int = 30,
    ):
        """
        Initialize a Python callable hook.

        Args:
            name: Hook identifier
            handler: Module path string or callable
            matcher: Glob pattern for tool name matching
            timeout: Execution timeout in seconds
        """
        super().__init__(name, matcher, timeout)
        self._handler_path = handler if isinstance(handler, str) else None
        self._callable: Optional[Callable] = handler if callable(handler) else None

    def _import_callable(self, path: str) -> Callable:
        """Import a callable from a module path."""
        parts = path.rsplit(".", 1)
        if len(parts) != 2:
            raise ImportError(f"Invalid callable path: {path}")
        module_path, func_name = parts
        module = importlib.import_module(module_path)
        return getattr(module, func_name)

    async def execute(
        self,
        function_name: str,
        arguments: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> HookResult:
        """Execute the Python callable hook."""
        if not self.matches(function_name):
            return HookResult.allow()

        # Lazy load callable
        if self._callable is None and self._handler_path:
            try:
                self._callable = self._import_callable(self._handler_path)
            except Exception as e:
                logger.error(f"[PythonCallableHook] Failed to import {self._handler_path}: {e}")
                # Fail closed on import error
                return HookResult.deny(reason=f"Hook import failed: {e}")

        if self._callable is None:
            return HookResult.allow()

        # Build HookEvent
        ctx = context or {}
        try:
            tool_input = json.loads(arguments) if arguments else {}
        except json.JSONDecodeError:
            tool_input = {"raw": arguments}

        event = HookEvent(
            hook_type=ctx.get("hook_type", "PreToolUse"),
            session_id=ctx.get("session_id", ""),
            orchestrator_id=ctx.get("orchestrator_id", ""),
            agent_id=ctx.get("agent_id"),
            timestamp=datetime.utcnow(),
            tool_name=function_name,
            tool_input=tool_input,
            tool_output=ctx.get("tool_output"),
        )

        try:
            # Execute with timeout
            if asyncio.iscoroutinefunction(self._callable):
                result = await asyncio.wait_for(
                    self._callable(event),
                    timeout=self.timeout,
                )
            else:
                # Sync callable - run in executor
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, self._callable, event),
                    timeout=self.timeout,
                )

            return self._normalize_result(result)

        except asyncio.TimeoutError:
            logger.warning(f"[PythonCallableHook] Hook {self.name} timed out for {function_name}")
            # Fail open on timeout
            return HookResult.allow()
        except Exception as e:
            logger.error(f"[PythonCallableHook] Hook {self.name} failed: {e}")
            # Fail open on execution error
            return HookResult.allow()

    def _normalize_result(self, result: Any) -> HookResult:
        """Normalize hook result to HookResult."""
        if isinstance(result, HookResult):
            return result
        if isinstance(result, dict):
            return HookResult.from_dict(result)
        if result is None:
            return HookResult.allow()
        # Unknown type - treat as allow
        logger.warning(f"[PythonCallableHook] Unknown result type: {type(result)}")
        return HookResult.allow()


class ExternalCommandHook(PatternHook):
    """Hook that invokes an external command via JSON stdin/stdout protocol.

    The external command receives:
    - stdin: JSON-encoded HookEvent
    - Environment variables: MASSGEN_HOOK_TYPE, MASSGEN_TOOL_NAME, etc.

    The command returns:
    - stdout: JSON-encoded HookResult
    """

    def __init__(
        self,
        name: str,
        handler: str,
        matcher: str = "*",
        timeout: int = 30,
    ):
        """
        Initialize an external command hook.

        Args:
            name: Hook identifier
            handler: Path to the executable script
            matcher: Glob pattern for tool name matching
            timeout: Execution timeout in seconds
        """
        super().__init__(name, matcher, timeout)
        self.handler_path = handler

    async def execute(
        self,
        function_name: str,
        arguments: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> HookResult:
        """Execute the external command hook."""
        if not self.matches(function_name):
            return HookResult.allow()

        ctx = context or {}
        try:
            tool_input = json.loads(arguments) if arguments else {}
        except json.JSONDecodeError:
            tool_input = {"raw": arguments}

        event = HookEvent(
            hook_type=ctx.get("hook_type", "PreToolUse"),
            session_id=ctx.get("session_id", ""),
            orchestrator_id=ctx.get("orchestrator_id", ""),
            agent_id=ctx.get("agent_id"),
            timestamp=datetime.utcnow(),
            tool_name=function_name,
            tool_input=tool_input,
            tool_output=ctx.get("tool_output"),
        )

        # Prepare environment
        env = os.environ.copy()
        env.update(
            {
                "MASSGEN_HOOK_TYPE": event.hook_type,
                "MASSGEN_TOOL_NAME": function_name,
                "MASSGEN_SESSION_ID": event.session_id,
                "MASSGEN_AGENT_ID": event.agent_id or "",
                "MASSGEN_ORCHESTRATOR_ID": event.orchestrator_id,
            },
        )

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                self.handler_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(event.to_json().encode()),
                timeout=self.timeout,
            )

            if stderr:
                logger.debug(f"[ExternalCommandHook] stderr from {self.name}: {stderr.decode()}")

            if proc.returncode != 0:
                logger.warning(f"[ExternalCommandHook] {self.name} exited with code {proc.returncode}")
                # Non-zero exit - fail open
                return HookResult.allow()

            # Parse JSON output
            try:
                result_dict = json.loads(stdout.decode())
                return HookResult.from_dict(result_dict)
            except json.JSONDecodeError as e:
                logger.warning(f"[ExternalCommandHook] Invalid JSON from {self.name}: {e}")
                return HookResult.allow()

        except asyncio.TimeoutError:
            logger.warning(f"[ExternalCommandHook] Hook {self.name} timed out for {function_name}")
            return HookResult.allow()
        except Exception as e:
            logger.error(f"[ExternalCommandHook] Hook {self.name} failed: {e}")
            return HookResult.allow()


class GeneralHookManager:
    """Extended hook manager supporting pattern-based matching and global/per-agent hooks.

    This manager supports:
    - Global hooks that apply to all agents
    - Per-agent hooks that can extend or override global hooks
    - Pattern-based matching on tool names
    - Aggregation of results from multiple hooks
    """

    def __init__(self):
        self._global_hooks: Dict[HookType, List[PatternHook]] = {
            HookType.PRE_TOOL_USE: [],
            HookType.POST_TOOL_USE: [],
        }
        self._agent_hooks: Dict[str, Dict[HookType, List[PatternHook]]] = {}
        self._agent_overrides: Dict[str, Dict[HookType, bool]] = {}

    def register_global_hook(self, hook_type: HookType, hook: PatternHook) -> None:
        """Register a hook that applies to all agents."""
        if hook_type not in self._global_hooks:
            self._global_hooks[hook_type] = []
        self._global_hooks[hook_type].append(hook)
        logger.debug(f"[GeneralHookManager] Registered global {hook_type.value} hook: {hook.name}")

    def register_agent_hook(
        self,
        agent_id: str,
        hook_type: HookType,
        hook: PatternHook,
        override: bool = False,
    ) -> None:
        """Register a hook for a specific agent.

        Args:
            agent_id: The agent identifier
            hook_type: Type of hook (PRE_TOOL_USE or POST_TOOL_USE)
            hook: The hook to register
            override: If True, disable global hooks for this event type
        """
        if agent_id not in self._agent_hooks:
            self._agent_hooks[agent_id] = {
                HookType.PRE_TOOL_USE: [],
                HookType.POST_TOOL_USE: [],
            }
            self._agent_overrides[agent_id] = {
                HookType.PRE_TOOL_USE: False,
                HookType.POST_TOOL_USE: False,
            }

        if hook_type not in self._agent_hooks[agent_id]:
            self._agent_hooks[agent_id][hook_type] = []

        self._agent_hooks[agent_id][hook_type].append(hook)

        if override:
            self._agent_overrides[agent_id][hook_type] = True

        logger.debug(
            f"[GeneralHookManager] Registered {hook_type.value} hook for agent {agent_id}: {hook.name}" f"{' (override)' if override else ''}",
        )

    def get_hooks_for_agent(
        self,
        agent_id: Optional[str],
        hook_type: HookType,
    ) -> List[PatternHook]:
        """Get all applicable hooks for an agent.

        If the agent has override=True for this hook type, only agent hooks are returned.
        Otherwise, global hooks are returned first, then agent hooks.
        """
        hooks = []

        # Check if agent overrides global hooks for this type
        if agent_id and agent_id in self._agent_overrides:
            if self._agent_overrides[agent_id].get(hook_type, False):
                # Override - only use agent hooks
                return list(self._agent_hooks.get(agent_id, {}).get(hook_type, []))

        # Add global hooks first
        hooks.extend(self._global_hooks.get(hook_type, []))

        # Add agent-specific hooks
        if agent_id and agent_id in self._agent_hooks:
            hooks.extend(self._agent_hooks[agent_id].get(hook_type, []))

        return hooks

    async def execute_hooks(
        self,
        hook_type: HookType,
        function_name: str,
        arguments: str,
        context: Dict[str, Any],
        tool_output: Optional[str] = None,
    ) -> HookResult:
        """Execute all matching hooks and aggregate results.

        For PreToolUse:
        - Any deny = deny
        - Modified inputs chain (each hook sees previous modifications)

        For PostToolUse:
        - All injection content is collected

        Args:
            hook_type: The type of hook (PRE_TOOL_USE or POST_TOOL_USE)
            function_name: Name of the tool being called
            arguments: JSON string of tool arguments
            context: Additional context (session_id, agent_id, etc.)
            tool_output: Tool output string (only for POST_TOOL_USE)

        Returns:
            Aggregated HookResult from all matching hooks
        """
        agent_id = context.get("agent_id")
        hooks = self.get_hooks_for_agent(agent_id, hook_type)

        # Add tool_output to context for PostToolUse hooks
        if tool_output is not None:
            context["tool_output"] = tool_output

        if not hooks:
            return HookResult.allow()

        # Filter to matching hooks
        matching_hooks = [h for h in hooks if h.matches(function_name)]

        if not matching_hooks:
            return HookResult.allow()

        final_result = HookResult.allow()
        modified_args = arguments
        all_injections: List[Dict[str, Any]] = []

        for hook in matching_hooks:
            try:
                # Update context with current args
                ctx = dict(context)
                result = await hook.execute(function_name, modified_args, ctx)

                # Handle deny - short circuit
                if not result.allowed or result.decision == "deny":
                    return HookResult.deny(
                        reason=result.reason or result.metadata.get("reason", f"Denied by hook {hook.name}"),
                    )

                # Handle ask decision
                if result.decision == "ask":
                    final_result.decision = "ask"
                    final_result.reason = result.reason

                # Chain modified arguments
                if result.modified_args is not None:
                    modified_args = result.modified_args
                elif result.updated_input is not None:
                    modified_args = json.dumps(result.updated_input)

                # Collect injections
                if result.inject:
                    all_injections.append(result.inject)

            except Exception as e:
                logger.error(f"[GeneralHookManager] Hook {hook.name} failed unexpectedly: {e}")
                # Fail open

        # Build final result
        final_result.modified_args = modified_args if modified_args != arguments else None
        if all_injections:
            # Combine injections
            combined_content = "\n".join(inj.get("content", "") for inj in all_injections if inj.get("content"))
            if combined_content:
                final_result.inject = {
                    "content": combined_content,
                    "strategy": all_injections[-1].get("strategy", "tool_result"),
                }

        return final_result

    def register_hooks_from_config(
        self,
        hooks_config: Dict[str, Any],
        agent_id: Optional[str] = None,
    ) -> None:
        """Register hooks from YAML configuration.

        Args:
            hooks_config: Hook configuration dictionary
            agent_id: If provided, register as agent hooks; otherwise as global hooks
        """
        hook_type_map = {
            "PreToolUse": HookType.PRE_TOOL_USE,
            "PostToolUse": HookType.POST_TOOL_USE,
        }

        for hook_type_name, hook_configs in hooks_config.items():
            if hook_type_name == "override":
                continue

            hook_type = hook_type_map.get(hook_type_name)
            if not hook_type:
                logger.warning(f"[GeneralHookManager] Unknown hook type: {hook_type_name}")
                continue

            # Handle override flag
            override = False
            if isinstance(hook_configs, dict):
                override = hook_configs.get("override", False)
                hook_configs = hook_configs.get("hooks", [])

            for config in hook_configs:
                hook = self._create_hook_from_config(config)
                if hook:
                    if agent_id:
                        self.register_agent_hook(agent_id, hook_type, hook, override)
                    else:
                        self.register_global_hook(hook_type, hook)

    def _create_hook_from_config(self, config: Dict[str, Any]) -> Optional[PatternHook]:
        """Create a hook instance from configuration."""
        handler = config.get("handler")
        if not handler:
            logger.warning("[GeneralHookManager] Hook config missing 'handler'")
            return None

        hook_handler_type = config.get("type", "python")
        matcher = config.get("matcher", "*")
        timeout = config.get("timeout", 30)
        name = f"{hook_handler_type}_{handler}"

        if hook_handler_type == "command":
            return ExternalCommandHook(
                name=name,
                handler=handler,
                matcher=matcher,
                timeout=timeout,
            )
        else:  # python
            return PythonCallableHook(
                name=name,
                handler=handler,
                matcher=matcher,
                timeout=timeout,
            )

    def clear_hooks(self) -> None:
        """Clear all registered hooks."""
        self._global_hooks = {
            HookType.PRE_TOOL_USE: [],
            HookType.POST_TOOL_USE: [],
        }
        self._agent_hooks.clear()
        self._agent_overrides.clear()


# =============================================================================
# Built-in Hooks for Migration
# =============================================================================


class MidStreamInjectionHook(PatternHook):
    """Built-in PostToolUse hook for mid-stream injection.

    This hook checks for pending updates from other agents during tool execution
    and injects their content into the tool result.

    Used by the orchestrator to inject answers from other agents mid-stream.
    """

    def __init__(
        self,
        name: str = "mid_stream_injection",
        injection_callback: Optional[Callable[[], Optional[str]]] = None,
    ):
        """
        Initialize the mid-stream injection hook.

        Args:
            name: Hook identifier
            injection_callback: Callable that returns injection content or None
        """
        super().__init__(name, matcher="*", timeout=5)
        self._injection_callback = injection_callback

    def set_callback(self, callback: Callable[[], Optional[str]]) -> None:
        """Set the injection callback dynamically."""
        self._injection_callback = callback

    async def execute(
        self,
        function_name: str,
        arguments: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> HookResult:
        """Execute the mid-stream injection hook."""
        if not self._injection_callback:
            return HookResult.allow()

        try:
            # Get injection content from callback
            content = self._injection_callback()
            if content:
                logger.debug(f"[MidStreamInjectionHook] Injecting content for {function_name}")
                return HookResult(
                    allowed=True,
                    inject={
                        "content": content,
                        "strategy": "tool_result",
                    },
                )
        except Exception as e:
            logger.warning(f"[MidStreamInjectionHook] Callback failed: {e}")

        return HookResult.allow()


class ReminderExtractionHook(PatternHook):
    """Built-in PostToolUse hook for reminder extraction.

    This hook extracts "reminder" fields from tool results (JSON) and injects
    them as user messages to make them more prominent to the agent.
    """

    def __init__(self, name: str = "reminder_extraction"):
        """Initialize the reminder extraction hook."""
        super().__init__(name, matcher="*", timeout=5)

    async def execute(
        self,
        function_name: str,
        arguments: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> HookResult:
        """Execute the reminder extraction hook."""
        tool_output = (context or {}).get("tool_output")
        if not tool_output:
            return HookResult.allow()

        reminder_text = None
        try:
            # Try to parse tool output as JSON
            result_dict = json.loads(tool_output)
            if isinstance(result_dict, dict):
                reminder_text = result_dict.get("reminder")
        except (json.JSONDecodeError, TypeError):
            pass

        if reminder_text and isinstance(reminder_text, str):
            logger.debug(f"[ReminderExtractionHook] Extracting reminder from {function_name}")
            return HookResult(
                allowed=True,
                inject={
                    "content": reminder_text,
                    "strategy": "user_message",
                },
            )

        return HookResult.allow()


class PermissionClientSession(ClientSession):
    """
    ClientSession subclass that intercepts tool calls to apply permission hooks.

    This inherits from ClientSession instead of wrapping it, which ensures
    compatibility with SDK type checking and attribute access.
    """

    def __init__(self, wrapped_session: ClientSession, permission_manager):
        """
        Initialize by copying state from an existing ClientSession.

        Args:
            wrapped_session: The actual ClientSession to copy state from
            permission_manager: Object with pre_tool_use_hook method for validation
        """
        # Store the permission manager
        self._permission_manager = permission_manager

        # Copy all attributes from the wrapped session to this instance
        # This is a bit hacky but necessary to preserve the session state
        self.__dict__.update(wrapped_session.__dict__)

        logger.debug(f"[PermissionClientSession] Created permission session from {id(wrapped_session)}")

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        read_timeout_seconds: timedelta | None = None,
        progress_callback: ProgressFnT | None = None,
    ) -> types.CallToolResult:
        """
        Override call_tool to apply permission hooks before calling the actual tool.
        """
        tool_args = arguments or {}

        # Log tool call for debugging
        logger.debug(f"[PermissionClientSession] Intercepted tool call: {name} with args: {tool_args}")

        # Apply permission hook if available
        if self._permission_manager and hasattr(self._permission_manager, "pre_tool_use_hook"):
            try:
                allowed, reason = await self._permission_manager.pre_tool_use_hook(name, tool_args)

                if not allowed:
                    error_msg = f"Permission denied for tool '{name}'"
                    if reason:
                        error_msg += f": {reason}"
                    logger.warning(f"🚫 [PermissionClientSession] {error_msg}")

                    # Return an error result instead of calling the tool
                    return types.CallToolResult(content=[types.TextContent(type="text", text=f"Error: {error_msg}")], isError=True)
                else:
                    logger.debug(f"[PermissionClientSession] Tool '{name}' permission check passed")

            except Exception as e:
                logger.error(f"[PermissionClientSession] Error in permission hook: {e}")
                # Continue with the call if hook fails - don't break functionality

        # Call the parent's call_tool method
        try:
            result = await super().call_tool(name=name, arguments=arguments, read_timeout_seconds=read_timeout_seconds, progress_callback=progress_callback)
            logger.debug(f"[PermissionClientSession] Tool '{name}' completed successfully")
            return result
        except Exception as e:
            logger.error(f"[PermissionClientSession] Tool '{name}' failed: {e}")
            raise


def convert_sessions_to_permission_sessions(sessions: List[ClientSession], permission_manager) -> List[PermissionClientSession]:
    """
    Convert a list of ClientSession objects to PermissionClientSession subclasses.

    Args:
        sessions: List of ClientSession objects to convert
        permission_manager: Object with pre_tool_use_hook method

    Returns:
        List of PermissionClientSession objects that apply permission hooks
    """
    logger.debug(f"[PermissionClientSession] Converting {len(sessions)} sessions to permission sessions")
    converted = []
    for session in sessions:
        # Create a new PermissionClientSession that inherits from ClientSession
        perm_session = PermissionClientSession(session, permission_manager)
        converted.append(perm_session)
    logger.debug(f"[PermissionClientSession] Successfully converted {len(converted)} sessions")
    return converted


__all__ = [
    # Core types
    "HookType",
    "HookEvent",
    "HookResult",
    # Legacy hook infrastructure
    "FunctionHook",
    "FunctionHookManager",
    # New general hook framework
    "PatternHook",
    "PythonCallableHook",
    "ExternalCommandHook",
    "GeneralHookManager",
    # Session-based hooks
    "PermissionClientSession",
    "convert_sessions_to_permission_sessions",
]
