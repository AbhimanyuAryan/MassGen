# -*- coding: utf-8 -*-
"""
Subagent Manager for MassGen

Manages the lifecycle of subagents: creation, workspace setup, execution, and result collection.
"""

import asyncio
import json
import logging
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from massgen.subagent.models import (
    SubagentConfig,
    SubagentPointer,
    SubagentResult,
    SubagentState,
)

logger = logging.getLogger(__name__)


class SubagentManager:
    """
    Manages subagent lifecycle, workspaces, and execution.

    Responsible for:
    - Creating isolated workspaces for subagents
    - Spawning and executing subagent tasks
    - Collecting and formatting results
    - Tracking active subagents
    - Cleanup on completion

    Subagents cannot spawn their own subagents (no nesting).
    """

    def __init__(
        self,
        parent_workspace: str,
        parent_agent_id: str,
        orchestrator_id: str,
        parent_backend_config: Dict[str, Any],
        max_concurrent: int = 3,
        default_timeout: int = 300,
    ):
        """
        Initialize SubagentManager.

        Args:
            parent_workspace: Path to parent agent's workspace
            parent_agent_id: ID of the parent agent
            orchestrator_id: ID of the orchestrator
            parent_backend_config: Backend configuration to inherit from parent
            max_concurrent: Maximum concurrent subagents (default 3)
            default_timeout: Default timeout in seconds (default 300)
        """
        self.parent_workspace = Path(parent_workspace)
        self.parent_agent_id = parent_agent_id
        self.orchestrator_id = orchestrator_id
        self.parent_backend_config = parent_backend_config
        self.max_concurrent = max_concurrent
        self.default_timeout = default_timeout

        # Base path for all subagent workspaces
        self.subagents_base = self.parent_workspace / "subagents"
        self.subagents_base.mkdir(parents=True, exist_ok=True)

        # Track active and completed subagents
        self._subagents: Dict[str, SubagentState] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)

        logger.info(
            f"[SubagentManager] Initialized for parent {parent_agent_id}, " f"workspace: {self.subagents_base}, max_concurrent: {max_concurrent}",
        )

    def _create_workspace(self, subagent_id: str) -> Path:
        """
        Create isolated workspace for a subagent.

        Args:
            subagent_id: Unique subagent identifier

        Returns:
            Path to the subagent's workspace directory
        """
        subagent_dir = self.subagents_base / subagent_id
        workspace = subagent_dir / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)

        # Create metadata file
        metadata = {
            "subagent_id": subagent_id,
            "parent_agent_id": self.parent_agent_id,
            "created_at": datetime.now().isoformat(),
            "workspace_path": str(workspace),
        }
        metadata_file = subagent_dir / "_metadata.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))

        logger.info(f"[SubagentManager] Created workspace for {subagent_id}: {workspace}")
        return workspace

    def _copy_context_files(
        self,
        subagent_id: str,
        context_files: List[str],
        workspace: Path,
    ) -> List[str]:
        """
        Copy context files from parent workspace to subagent workspace.

        Args:
            subagent_id: Subagent identifier
            context_files: List of relative paths to copy
            workspace: Subagent workspace path

        Returns:
            List of successfully copied files
        """
        copied = []
        for rel_path in context_files:
            src = self.parent_workspace / rel_path
            if not src.exists():
                logger.warning(f"[SubagentManager] Context file not found: {src}")
                continue

            # Preserve directory structure
            dst = workspace / rel_path
            dst.parent.mkdir(parents=True, exist_ok=True)

            if src.is_file():
                shutil.copy2(src, dst)
                copied.append(rel_path)
            elif src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
                copied.append(rel_path)

        logger.info(f"[SubagentManager] Copied {len(copied)} context files for {subagent_id}")
        return copied

    def _get_workspace_files(self, subagent_id: str) -> List[str]:
        """
        Get list of files created in subagent workspace.

        Args:
            subagent_id: Subagent identifier

        Returns:
            List of relative file paths
        """
        workspace = self.subagents_base / subagent_id / "workspace"
        if not workspace.exists():
            return []

        files = []
        for path in workspace.rglob("*"):
            if path.is_file():
                rel_path = path.relative_to(workspace)
                files.append(str(rel_path))

        return files

    def _build_subagent_system_prompt(self, config: SubagentConfig) -> str:
        """
        Build system prompt for subagent.

        Subagents get a minimal system prompt focused on their specific task.
        They cannot spawn their own subagents.

        Args:
            config: Subagent configuration

        Returns:
            System prompt string
        """
        base_prompt = config.system_prompt or "You are a helpful assistant working on a specific task."

        subagent_prompt = f"""{base_prompt}

## Subagent Context

You are a subagent spawned to work on a specific task. Your workspace is isolated and independent.

**Important:**
- Focus only on the task you were given
- Write your final answer to answer.txt in your workspace
- Create any necessary files in your workspace
- You cannot spawn additional subagents
- Your results will be collected when you complete the task

**Your Task:**
{config.task}
"""
        return subagent_prompt

    async def _execute_subagent(
        self,
        config: SubagentConfig,
        workspace: Path,
    ) -> SubagentResult:
        """
        Execute a subagent task.

        Creates a ConfigurableAgent for the subagent and runs it with the task.

        Args:
            config: Subagent configuration
            workspace: Path to subagent workspace

        Returns:
            SubagentResult with execution outcome
        """
        start_time = time.time()

        try:
            # Import here to avoid circular imports
            from massgen.agent_config import AgentConfig
            from massgen.chat_agent import ConfigurableAgent
            from massgen.cli import create_backend

            # Build backend config for subagent
            backend_config = self.parent_backend_config.copy()

            # Override model if specified
            if config.model:
                backend_config["model"] = config.model

            # Set workspace for subagent
            backend_config["cwd"] = str(workspace)

            # Disable subagent capability for subagents (no nesting)
            backend_config["_is_subagent"] = True

            # Get backend type
            backend_type = backend_config.get("type", "openai")

            # Create backend
            backend = create_backend(backend_type, **backend_config)

            # Create agent config
            agent_config = AgentConfig(
                backend_params=backend_config,
                agent_id=config.id,
            )
            agent_config._custom_system_instruction = self._build_subagent_system_prompt(config)

            # Create agent
            agent = ConfigurableAgent(
                config=agent_config,
                backend=backend,
            )

            # Execute the task
            # Use a simple chat interaction - subagent processes the task
            messages = [{"role": "user", "content": config.task}]

            answer = ""
            async for chunk in agent.chat(messages):
                if hasattr(chunk, "content") and chunk.content:
                    answer += chunk.content

            execution_time = time.time() - start_time

            # Check for answer.txt in workspace
            answer_file = workspace / "answer.txt"
            if answer_file.exists():
                answer = answer_file.read_text()

            # Get files created
            files_created = self._get_workspace_files(config.id)

            return SubagentResult.create_success(
                subagent_id=config.id,
                answer=answer,
                workspace_path=str(workspace),
                files_created=files_created,
                execution_time_seconds=execution_time,
            )

        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            files_created = self._get_workspace_files(config.id)
            return SubagentResult.create_timeout(
                subagent_id=config.id,
                workspace_path=str(workspace),
                files_created=files_created,
                timeout_seconds=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"[SubagentManager] Error executing subagent {config.id}: {e}")
            return SubagentResult.create_error(
                subagent_id=config.id,
                error=str(e),
                workspace_path=str(workspace),
                execution_time_seconds=execution_time,
            )

    async def spawn_subagent(
        self,
        task: str,
        subagent_id: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        context_files: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
    ) -> SubagentResult:
        """
        Spawn a single subagent to work on a task.

        Args:
            task: The task for the subagent
            subagent_id: Optional custom ID
            model: Optional model override
            timeout_seconds: Optional timeout (uses default if not specified)
            context_files: Optional files to copy to subagent workspace
            system_prompt: Optional custom system prompt

        Returns:
            SubagentResult with execution outcome
        """
        # Create config
        config = SubagentConfig.create(
            task=task,
            parent_agent_id=self.parent_agent_id,
            subagent_id=subagent_id,
            model=model,
            timeout_seconds=timeout_seconds or self.default_timeout,
            context_files=context_files or [],
            system_prompt=system_prompt,
        )

        logger.info(f"[SubagentManager] Spawning subagent {config.id} for task: {task[:100]}...")

        # Create workspace
        workspace = self._create_workspace(config.id)

        # Copy context files if specified
        if config.context_files:
            self._copy_context_files(config.id, config.context_files, workspace)

        # Track state
        state = SubagentState(
            config=config,
            status="running",
            workspace_path=str(workspace),
            started_at=datetime.now(),
        )
        self._subagents[config.id] = state

        # Execute with semaphore and timeout
        async with self._semaphore:
            try:
                result = await asyncio.wait_for(
                    self._execute_subagent(config, workspace),
                    timeout=config.timeout_seconds,
                )
            except asyncio.TimeoutError:
                files_created = self._get_workspace_files(config.id)
                result = SubagentResult.create_timeout(
                    subagent_id=config.id,
                    workspace_path=str(workspace),
                    files_created=files_created,
                    timeout_seconds=config.timeout_seconds,
                )

        # Update state
        state.status = "completed" if result.success else ("timeout" if result.status == "timeout" else "failed")
        state.result = result

        logger.info(
            f"[SubagentManager] Subagent {config.id} finished with status: {result.status}, " f"time: {result.execution_time_seconds:.2f}s",
        )

        return result

    async def spawn_parallel(
        self,
        tasks: List[Dict[str, Any]],
        timeout_seconds: Optional[int] = None,
    ) -> List[SubagentResult]:
        """
        Spawn multiple subagents to run in parallel.

        Args:
            tasks: List of task configurations, each with:
                   - task (required): Task description
                   - subagent_id (optional): Custom ID
                   - model (optional): Model override
                   - context_files (optional): Files to copy
            timeout_seconds: Optional timeout for all subagents

        Returns:
            List of SubagentResults in same order as input tasks
        """
        logger.info(f"[SubagentManager] Spawning {len(tasks)} subagents in parallel")

        # Create coroutines for each task
        coroutines = []
        for task_config in tasks:
            coro = self.spawn_subagent(
                task=task_config["task"],
                subagent_id=task_config.get("subagent_id"),
                model=task_config.get("model"),
                timeout_seconds=timeout_seconds or task_config.get("timeout_seconds"),
                context_files=task_config.get("context_files"),
                system_prompt=task_config.get("system_prompt"),
            )
            coroutines.append(coro)

        # Execute all in parallel (semaphore limits concurrency)
        results = await asyncio.gather(*coroutines, return_exceptions=True)

        # Convert exceptions to error results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                task_id = tasks[i].get("subagent_id", f"sub_{i}")
                final_results.append(
                    SubagentResult.create_error(
                        subagent_id=task_id,
                        error=str(result),
                    ),
                )
            else:
                final_results.append(result)

        return final_results

    def list_subagents(self) -> List[Dict[str, Any]]:
        """
        List all subagents spawned by this manager.

        Returns:
            List of subagent info dictionaries
        """
        return [
            {
                "subagent_id": subagent_id,
                "status": state.status,
                "workspace": state.workspace_path,
                "started_at": state.started_at.isoformat() if state.started_at else None,
                "task": state.config.task[:100] + ("..." if len(state.config.task) > 100 else ""),
            }
            for subagent_id, state in self._subagents.items()
        ]

    def get_subagent_result(self, subagent_id: str) -> Optional[SubagentResult]:
        """
        Get result for a specific subagent.

        Args:
            subagent_id: Subagent identifier

        Returns:
            SubagentResult if subagent exists and completed, None otherwise
        """
        state = self._subagents.get(subagent_id)
        if state and state.result:
            return state.result
        return None

    def get_subagent_pointer(self, subagent_id: str) -> Optional[SubagentPointer]:
        """
        Get pointer for a subagent (for plan.json tracking).

        Args:
            subagent_id: Subagent identifier

        Returns:
            SubagentPointer if subagent exists, None otherwise
        """
        state = self._subagents.get(subagent_id)
        if not state:
            return None

        pointer = SubagentPointer(
            id=subagent_id,
            task=state.config.task,
            workspace=state.workspace_path,
            status=state.status,
            created_at=state.config.created_at,
        )

        if state.result:
            pointer.mark_completed(state.result)

        return pointer

    def cleanup_subagent(self, subagent_id: str, remove_workspace: bool = False) -> bool:
        """
        Clean up a subagent.

        Args:
            subagent_id: Subagent identifier
            remove_workspace: If True, also remove the workspace directory

        Returns:
            True if cleanup successful, False if subagent not found
        """
        if subagent_id not in self._subagents:
            return False

        if remove_workspace:
            workspace_dir = self.subagents_base / subagent_id
            if workspace_dir.exists():
                shutil.rmtree(workspace_dir)
                logger.info(f"[SubagentManager] Removed workspace for {subagent_id}")

        del self._subagents[subagent_id]
        return True

    def cleanup_all(self, remove_workspaces: bool = False) -> int:
        """
        Clean up all subagents.

        Args:
            remove_workspaces: If True, also remove workspace directories

        Returns:
            Number of subagents cleaned up
        """
        count = len(self._subagents)
        subagent_ids = list(self._subagents.keys())

        for subagent_id in subagent_ids:
            self.cleanup_subagent(subagent_id, remove_workspace=remove_workspaces)

        return count
