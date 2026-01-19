# -*- coding: utf-8 -*-
"""
Setup Wizard for MassGen TUI.

Provides an interactive wizard for configuring API keys and initial setup.
This replaces the questionary-based CLI setup with a Textual TUI experience.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.widgets import Checkbox, Input, Label, Static

from .wizard_base import StepComponent, WizardModal, WizardState, WizardStep
from .wizard_steps import SaveLocationStep, WelcomeStep


def _setup_log(msg: str) -> None:
    """Log to TUI debug file."""
    try:
        import logging

        log = logging.getLogger("massgen.tui.debug")
        if not log.handlers:
            handler = logging.FileHandler("/tmp/massgen_tui_debug.log", mode="a")
            handler.setFormatter(logging.Formatter("%(asctime)s [SETUP] %(message)s", datefmt="%H:%M:%S"))
            log.addHandler(handler)
            log.setLevel(logging.DEBUG)
            log.propagate = False
        log.debug(msg)
    except Exception:
        pass


class SetupWelcomeStep(WelcomeStep):
    """Welcome step customized for setup wizard."""

    def __init__(self, wizard_state: WizardState, **kwargs):
        super().__init__(
            wizard_state,
            title="Welcome to MassGen Setup",
            subtitle="Configure MassGen for first use",
            features=[
                "Detect and configure API keys",
                "Set up Docker for code execution",
                "Install additional skills",
            ],
            **kwargs,
        )


class ProviderSelectionStep(StepComponent):
    """Step for selecting which providers to configure.

    Shows all providers with their current configuration status.
    Users can select multiple unconfigured providers to set up.
    """

    def __init__(
        self,
        wizard_state: WizardState,
        *,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        super().__init__(wizard_state, id=id, classes=classes)
        self._checkboxes: Dict[str, Checkbox] = {}
        self._providers: List[tuple] = []  # (provider_id, name, is_configured, env_var)

    def _load_providers(self) -> None:
        """Load provider information from ConfigBuilder."""
        try:
            from massgen.config_builder import ConfigBuilder

            builder = ConfigBuilder()
            api_keys = builder.detect_api_keys()

            for provider_id, provider_info in builder.PROVIDERS.items():
                # Skip local models and Claude Code
                if provider_id in ("ollama", "llamacpp", "claude_code"):
                    continue

                name = provider_info.get("name", provider_id)
                env_var = provider_info.get("env_var", "")
                is_configured = api_keys.get(provider_id, False)

                self._providers.append((provider_id, name, is_configured, env_var))

        except Exception as e:
            _setup_log(f"ProviderSelectionStep._load_providers error: {e}")

    def compose(self) -> ComposeResult:
        self._load_providers()

        yield Label("Select providers to configure:", classes="text-input-label")
        yield Label("(Already configured providers are shown with [green]|[/green])", classes="password-hint")

        with ScrollableContainer(classes="provider-list"):
            for provider_id, name, is_configured, env_var in self._providers:
                status = "[green]|[/green]" if is_configured else "[dim]|[/dim]"
                status_text = "(configured)" if is_configured else "(needs setup)"

                checkbox = Checkbox(
                    f"{status} {name} {status_text}",
                    value=False,  # Start unchecked, user selects what to configure
                    id=f"provider_cb_{provider_id}",
                    disabled=is_configured,  # Can't re-configure already set up providers here
                )
                self._checkboxes[provider_id] = checkbox
                yield checkbox

    def get_value(self) -> List[str]:
        """Return list of selected provider IDs."""
        return [pid for pid, cb in self._checkboxes.items() if cb.value]

    def set_value(self, value: Any) -> None:
        if isinstance(value, list):
            for pid, cb in self._checkboxes.items():
                cb.value = pid in value

    def validate(self) -> Optional[str]:
        # Allow proceeding with no selection (user may already have all keys configured)
        return None


class DynamicApiKeyStep(StepComponent):
    """Dynamic step for entering an API key for a specific provider.

    This step is created dynamically for each selected provider.
    """

    def __init__(
        self,
        wizard_state: WizardState,
        provider_id: str,
        provider_name: str,
        env_var: str,
        *,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        super().__init__(wizard_state, id=id, classes=classes)
        self.provider_id = provider_id
        self.provider_name = provider_name
        self.env_var = env_var
        self._input: Optional[Input] = None

    def compose(self) -> ComposeResult:
        with Container(classes="password-container"):
            yield Label(f"Enter API Key for {self.provider_name}", classes="password-label")
            yield Label(f"Environment variable: {self.env_var}", classes="password-hint")

            self._input = Input(
                placeholder=f"Enter your {self.provider_name} API key...",
                password=True,
                classes="password-input",
                id=f"api_key_input_{self.provider_id}",
            )
            yield self._input

            yield Label(
                "Your API key will be saved securely in your .env file",
                classes="password-hint",
            )

    def get_value(self) -> Dict[str, str]:
        """Return dict with env_var: api_key."""
        if self._input and self._input.value:
            return {self.env_var: self._input.value}
        return {}

    def set_value(self, value: Any) -> None:
        if isinstance(value, dict) and self.env_var in value:
            if self._input:
                self._input.value = value[self.env_var]

    def validate(self) -> Optional[str]:
        if not self._input or not self._input.value.strip():
            return f"Please enter your {self.provider_name} API key"
        return None


class DockerSetupStep(StepComponent):
    """Step for setting up Docker for code execution.

    Shows Docker diagnostics and allows selecting which images to pull.
    """

    DEFAULT_CSS = """
    DockerSetupStep {
        width: 100%;
        height: 100%;
    }

    DockerSetupStep .docker-container {
        width: 100%;
        height: auto;
        padding: 1 2;
    }

    DockerSetupStep .docker-status {
        margin-bottom: 1;
    }

    DockerSetupStep .docker-status-ok {
        color: $success;
    }

    DockerSetupStep .docker-status-error {
        color: $error;
    }

    DockerSetupStep .docker-status-warning {
        color: $warning;
    }

    DockerSetupStep .docker-section-title {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
    }

    DockerSetupStep .docker-image-item {
        margin: 0 0 1 2;
    }
    """

    AVAILABLE_IMAGES = [
        {
            "name": "ghcr.io/massgen/mcp-runtime-sudo:latest",
            "description": "Sudo image (recommended - allows package installation)",
            "default": True,
        },
        {
            "name": "ghcr.io/massgen/mcp-runtime:latest",
            "description": "Standard image (no sudo access)",
            "default": False,
        },
    ]

    def __init__(
        self,
        wizard_state: WizardState,
        *,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        super().__init__(wizard_state, id=id, classes=classes)
        self._diagnostics = None
        self._checkboxes: Dict[str, Checkbox] = {}
        self._selected_images: List[str] = []

    def _load_diagnostics(self) -> None:
        """Load Docker diagnostics."""
        try:
            from massgen.utils.docker_diagnostics import diagnose_docker

            self._diagnostics = diagnose_docker(check_images=True)
        except Exception as e:
            _setup_log(f"DockerSetupStep: Failed to load diagnostics: {e}")
            self._diagnostics = None

    def compose(self) -> ComposeResult:
        self._load_diagnostics()

        with ScrollableContainer(classes="docker-container"):
            # Status section
            yield Label("Docker Status:", classes="docker-section-title")

            if self._diagnostics is None:
                yield Label("  ✗ Could not check Docker status", classes="docker-status docker-status-error")
                return

            # Show diagnostics
            version_info = f" ({self._diagnostics.docker_version})" if self._diagnostics.docker_version else ""
            if self._diagnostics.binary_installed:
                yield Label(f"  ✓ Docker binary installed{version_info}", classes="docker-status docker-status-ok")
            else:
                yield Label("  ✗ Docker binary not installed", classes="docker-status docker-status-error")

            if self._diagnostics.pip_library_installed:
                yield Label("  ✓ Docker Python library", classes="docker-status docker-status-ok")
            else:
                yield Label("  ✗ Docker Python library not installed", classes="docker-status docker-status-error")

            if self._diagnostics.daemon_running:
                yield Label("  ✓ Docker daemon running", classes="docker-status docker-status-ok")
            else:
                yield Label("  ✗ Docker daemon not running", classes="docker-status docker-status-error")

            if self._diagnostics.has_permissions:
                yield Label("  ✓ Permissions OK", classes="docker-status docker-status-ok")
            else:
                yield Label("  ✗ Permission denied", classes="docker-status docker-status-error")

            # If Docker not available, show error
            if not self._diagnostics.is_available:
                yield Static("")
                yield Label(f"Error: {self._diagnostics.error_message}", classes="docker-status docker-status-error")
                yield Static("")
                yield Label("To fix this:", classes="docker-section-title")
                for step in self._diagnostics.resolution_steps:
                    yield Label(f"  • {step}", classes="docker-status")
                return

            # Images section
            yield Static("")
            yield Label("Docker Images:", classes="docker-section-title")

            missing_images = []
            for img in self.AVAILABLE_IMAGES:
                img_name = img["name"]
                is_installed = self._diagnostics.images_available.get(img_name, False)

                if is_installed:
                    yield Label(f"  ✓ {img_name}", classes="docker-status docker-status-ok")
                else:
                    yield Label(f"  ✗ {img_name}", classes="docker-status docker-status-error")
                    missing_images.append(img)

            # If all images installed, we're done
            if not missing_images:
                yield Static("")
                yield Label("All Docker images are already installed!", classes="docker-status docker-status-ok")
                return

            # Offer to pull missing images
            yield Static("")
            yield Label("Select images to pull:", classes="docker-section-title")

            for img in missing_images:
                img_name = img["name"]
                cb = Checkbox(
                    f"{img['description']}",
                    value=img.get("default", False),
                    id=f"docker_img_{img_name.replace('/', '_').replace(':', '_').replace('.', '_')}",
                )
                self._checkboxes[img_name] = cb
                if img.get("default", False):
                    self._selected_images.append(img_name)
                with Horizontal(classes="docker-image-item"):
                    yield cb

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox toggle."""
        for img_name, cb in self._checkboxes.items():
            if cb.id == event.checkbox.id:
                if event.value and img_name not in self._selected_images:
                    self._selected_images.append(img_name)
                elif not event.value and img_name in self._selected_images:
                    self._selected_images.remove(img_name)
                break

    def get_value(self) -> Dict[str, Any]:
        return {
            "available": self._diagnostics.is_available if self._diagnostics else False,
            "images_to_pull": self._selected_images,
        }

    def set_value(self, value: Any) -> None:
        if isinstance(value, dict):
            self._selected_images = value.get("images_to_pull", [])
            for img_name, cb in self._checkboxes.items():
                cb.value = img_name in self._selected_images


class SkillsSetupStep(StepComponent):
    """Step for installing additional skills.

    Shows current skills status and allows selecting packages to install.
    """

    DEFAULT_CSS = """
    SkillsSetupStep {
        width: 100%;
        height: 100%;
    }

    SkillsSetupStep .skills-container {
        width: 100%;
        height: auto;
        padding: 1 2;
    }

    SkillsSetupStep .skills-status-ok {
        color: $success;
    }

    SkillsSetupStep .skills-status-error {
        color: $error;
    }

    SkillsSetupStep .skills-section-title {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
    }

    SkillsSetupStep .skills-item {
        margin: 0 0 1 2;
    }

    SkillsSetupStep .skills-description {
        color: $text-muted;
        margin-left: 4;
        margin-bottom: 1;
    }
    """

    def __init__(
        self,
        wizard_state: WizardState,
        *,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        super().__init__(wizard_state, id=id, classes=classes)
        self._packages_status = None
        self._skills_info = None
        self._checkboxes: Dict[str, Checkbox] = {}
        self._selected_packages: List[str] = []

    def _load_skills_status(self) -> None:
        """Load skills status."""
        try:
            from massgen.utils.skills_installer import (
                check_skill_packages_installed,
                list_available_skills,
            )

            self._skills_info = list_available_skills()
            self._packages_status = check_skill_packages_installed()
        except Exception as e:
            _setup_log(f"SkillsSetupStep: Failed to load skills status: {e}")
            self._skills_info = None
            self._packages_status = None

    def compose(self) -> ComposeResult:
        self._load_skills_status()

        with ScrollableContainer(classes="skills-container"):
            # Summary
            yield Label("Skills Status:", classes="skills-section-title")

            if self._skills_info is None:
                yield Label("  ✗ Could not check skills status", classes="skills-status-error")
                return

            builtin = self._skills_info.get("builtin", [])
            user = self._skills_info.get("user", [])
            project = self._skills_info.get("project", [])
            installed_count = len(user) + len(project)
            total = len(builtin) + installed_count

            yield Label(f"  {total} skill(s) available ({len(builtin)} built-in, {installed_count} installed)", classes="skills-item")

            # Packages section
            yield Static("")
            yield Label("Skill Packages:", classes="skills-section-title")

            if self._packages_status is None:
                yield Label("  Could not check package status", classes="skills-status-error")
                return

            packages_to_install = []
            for pkg_id, pkg in self._packages_status.items():
                if pkg["installed"]:
                    count_info = f" ({pkg.get('skill_count', 0)} skills)" if pkg.get("skill_count") else ""
                    yield Label(f"  ✓ {pkg['name']} [installed{count_info}]", classes="skills-status-ok")
                else:
                    yield Label(f"  ✗ {pkg['name']} [not installed]", classes="skills-status-error")
                    packages_to_install.append((pkg_id, pkg))
                yield Label(f"      {pkg['description']}", classes="skills-description")

            # If all packages installed, we're done
            if not packages_to_install:
                yield Static("")
                yield Label("All skill packages are already installed!", classes="skills-status-ok")
                return

            # Offer to install missing packages
            yield Static("")
            yield Label("Select packages to install:", classes="skills-section-title")

            for pkg_id, pkg in packages_to_install:
                cb = Checkbox(
                    f"Install {pkg['name']}",
                    value=True,  # Default to install
                    id=f"skills_pkg_{pkg_id}",
                )
                self._checkboxes[pkg_id] = cb
                self._selected_packages.append(pkg_id)
                with Horizontal(classes="skills-item"):
                    yield cb

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox toggle."""
        for pkg_id, cb in self._checkboxes.items():
            if cb.id == event.checkbox.id:
                if event.value and pkg_id not in self._selected_packages:
                    self._selected_packages.append(pkg_id)
                elif not event.value and pkg_id in self._selected_packages:
                    self._selected_packages.remove(pkg_id)
                break

    def get_value(self) -> Dict[str, Any]:
        return {
            "packages_to_install": self._selected_packages,
        }

    def set_value(self, value: Any) -> None:
        if isinstance(value, dict):
            self._selected_packages = value.get("packages_to_install", [])
            for pkg_id, cb in self._checkboxes.items():
                cb.value = pkg_id in self._selected_packages


class SetupCompleteStep(StepComponent):
    """Final step showing setup completion and next actions."""

    DEFAULT_CSS = """
    SetupCompleteStep {
        align: center middle;
        width: 100%;
        height: 100%;
    }

    SetupCompleteStep .complete-container {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 2 4;
    }

    SetupCompleteStep .complete-icon {
        text-align: center;
        width: 100%;
        color: $success;
        text-style: bold;
        margin-bottom: 1;
    }

    SetupCompleteStep .complete-title {
        text-align: center;
        width: 100%;
        text-style: bold;
        color: $primary;
        margin-bottom: 2;
    }

    SetupCompleteStep .complete-message {
        text-align: center;
        width: 100%;
        color: $text;
        margin-bottom: 1;
    }

    SetupCompleteStep .complete-next-steps {
        width: 100%;
        color: $text-muted;
        margin-top: 1;
    }
    """

    def __init__(
        self,
        wizard_state: WizardState,
        *,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        super().__init__(wizard_state, id=id, classes=classes)

    def compose(self) -> ComposeResult:
        with Vertical(classes="complete-container"):
            yield Label("✓", classes="complete-icon")
            yield Label("Setup Complete!", classes="complete-title")

            # Show what was configured
            configured = self.wizard_state.get("configured_providers", [])
            save_location = self.wizard_state.get("save_location", ".env")
            docker_images = self.wizard_state.get("docker_images_pulled", [])
            skills_installed = self.wizard_state.get("skills_installed", [])

            if configured:
                yield Label(f"✓ Configured {len(configured)} provider(s)", classes="complete-message")

            if save_location:
                yield Label(f"✓ API keys saved to: {save_location}", classes="complete-message")

            if docker_images:
                yield Label(f"✓ Pulled {len(docker_images)} Docker image(s)", classes="complete-message")

            if skills_installed:
                yield Label(f"✓ Installed {len(skills_installed)} skill package(s)", classes="complete-message")

            yield Static("")
            yield Label("Next steps:", classes="complete-next-steps")
            yield Label("  • Run 'massgen --quickstart' to create a config", classes="complete-next-steps")
            yield Label("  • Or run 'massgen --config your_config.yaml' to start", classes="complete-next-steps")

    def get_value(self) -> bool:
        return True


class SetupWizard(WizardModal):
    """Setup wizard for configuring API keys, Docker, and skills.

    Flow:
    1. Welcome
    2. Provider selection
    3. API key input for each selected provider (dynamic)
    4. Save location selection
    5. Docker setup (optional)
    6. Skills installation (optional)
    7. Complete
    """

    def __init__(
        self,
        *,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self._dynamic_steps_added = False
        self._providers_info: Dict[str, tuple] = {}  # provider_id -> (name, env_var)

    def _load_providers_info(self) -> None:
        """Load provider information for dynamic step creation."""
        try:
            from massgen.config_builder import ConfigBuilder

            builder = ConfigBuilder()
            for provider_id, provider_info in builder.PROVIDERS.items():
                if provider_id in ("ollama", "llamacpp", "claude_code"):
                    continue
                name = provider_info.get("name", provider_id)
                env_var = provider_info.get("env_var", "")
                self._providers_info[provider_id] = (name, env_var)
        except Exception as e:
            _setup_log(f"SetupWizard._load_providers_info error: {e}")

    def get_steps(self) -> List[WizardStep]:
        """Return the initial steps. Dynamic steps are added after provider selection."""
        self._load_providers_info()

        return [
            WizardStep(
                id="welcome",
                title="Welcome to MassGen Setup",
                description="Configure API keys for AI providers",
                component_class=SetupWelcomeStep,
            ),
            WizardStep(
                id="select_providers",
                title="Select Providers",
                description="Choose which providers to configure",
                component_class=ProviderSelectionStep,
            ),
            # Dynamic API key steps will be inserted here
            WizardStep(
                id="save_location",
                title="Save Location",
                description="Choose where to save your API keys",
                component_class=SaveLocationStep,
            ),
            WizardStep(
                id="docker_setup",
                title="Docker Setup",
                description="Configure Docker for code execution",
                component_class=DockerSetupStep,
            ),
            WizardStep(
                id="skills_setup",
                title="Skills Installation",
                description="Install additional MassGen skills",
                component_class=SkillsSetupStep,
            ),
            WizardStep(
                id="complete",
                title="Setup Complete",
                description="Your setup has been configured",
                component_class=SetupCompleteStep,
            ),
        ]

    async def action_next_step(self) -> None:
        """Override to handle dynamic step generation after provider selection."""
        if not self._current_component:
            return

        step = self._steps[self.state.current_step_idx]

        # Validate current step
        error = self._current_component.validate()
        if error:
            self._show_error(error)
            self.state.set_error(step.id, error)
            return

        # Save current step data
        value = self._current_component.get_value()
        self.state.step_data[step.id] = value
        self.state.clear_error(step.id)

        # If we just completed provider selection, create dynamic API key steps
        if step.id == "select_providers" and not self._dynamic_steps_added:
            selected_providers = value if isinstance(value, list) else []
            _setup_log(f"SetupWizard: Selected providers: {selected_providers}")

            if selected_providers:
                # Insert dynamic steps before save_location
                insert_idx = self.state.current_step_idx + 1

                for provider_id in selected_providers:
                    if provider_id in self._providers_info:
                        name, env_var = self._providers_info[provider_id]

                        # Create a custom component class for this provider
                        def make_component_class(pid, pname, penv):
                            class DynamicStep(DynamicApiKeyStep):
                                def __init__(self, wizard_state, **kwargs):
                                    super().__init__(wizard_state, pid, pname, penv, **kwargs)

                            return DynamicStep

                        new_step = WizardStep(
                            id=f"api_key_{provider_id}",
                            title=f"Configure {name}",
                            description=f"Enter your {name} API key",
                            component_class=make_component_class(provider_id, name, env_var),
                        )
                        self._steps.insert(insert_idx, new_step)
                        insert_idx += 1

            self._dynamic_steps_added = True

        # Find next step
        next_idx = self._find_next_step(self.state.current_step_idx + 1)
        if next_idx >= len(self._steps):
            await self._complete_wizard()
        else:
            await self._show_step(next_idx)

    async def on_wizard_complete(self) -> Any:
        """Save the API keys to the selected location."""
        _setup_log("SetupWizard.on_wizard_complete: Saving API keys")

        # Collect all API keys from dynamic steps
        collected_keys: Dict[str, str] = {}
        configured_providers: List[str] = []

        for step_id, step_data in self.state.step_data.items():
            if step_id.startswith("api_key_") and isinstance(step_data, dict):
                collected_keys.update(step_data)
                provider_id = step_id.replace("api_key_", "")
                configured_providers.append(provider_id)

        # Get save location
        save_location = self.state.get("save_location", ".env")
        _setup_log(f"SetupWizard: Saving to {save_location}, keys: {list(collected_keys.keys())}")

        # Determine target path
        if save_location == "~/.massgen/.env":
            env_dir = Path.home() / ".massgen"
            env_dir.mkdir(parents=True, exist_ok=True)
            env_path = env_dir / ".env"
        elif save_location == "~/.config/massgen/.env":
            env_dir = Path.home() / ".config" / "massgen"
            env_dir.mkdir(parents=True, exist_ok=True)
            env_path = env_dir / ".env"
        elif save_location == "configs/.env":
            env_dir = Path("configs")
            env_dir.mkdir(parents=True, exist_ok=True)
            env_path = env_dir / ".env"
        else:
            env_path = Path(".env")

        # Merge with existing .env if present
        existing_content = {}
        if env_path.exists():
            try:
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            existing_content[key.strip()] = value.strip()
            except Exception as e:
                _setup_log(f"SetupWizard: Could not read existing .env: {e}")

        # Merge: existing + new (new overwrites)
        existing_content.update(collected_keys)
        final_keys = existing_content

        # Write .env file
        try:
            with open(env_path, "w") as f:
                f.write("# MassGen API Keys\n")
                f.write("# Generated by MassGen TUI Setup Wizard\n\n")

                for env_var, api_key in sorted(final_keys.items()):
                    f.write(f"{env_var}={api_key}\n")

            _setup_log(f"SetupWizard: Saved API keys to {env_path.absolute()}")

            # Reload environment variables
            load_dotenv(env_path, override=True)

        except Exception as e:
            _setup_log(f"SetupWizard: Failed to save .env: {e}")
            return {"success": False, "error": str(e)}

        # Store info for complete step
        self.state.set("configured_providers", configured_providers)
        self.state.set("save_location", str(env_path.absolute()))

        # Handle Docker image pulls if requested
        docker_data = self.state.get("docker_setup", {})
        images_to_pull = docker_data.get("images_to_pull", []) if isinstance(docker_data, dict) else []
        pulled_images = []

        if images_to_pull:
            _setup_log(f"SetupWizard: Pulling Docker images: {images_to_pull}")
            try:
                import subprocess

                for image in images_to_pull:
                    _setup_log(f"SetupWizard: Pulling {image}")
                    result = subprocess.run(
                        ["docker", "pull", image],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if result.returncode == 0:
                        pulled_images.append(image)
                        _setup_log(f"SetupWizard: Successfully pulled {image}")
                    else:
                        _setup_log(f"SetupWizard: Failed to pull {image}: {result.stderr}")
            except Exception as e:
                _setup_log(f"SetupWizard: Docker pull failed: {e}")

        self.state.set("docker_images_pulled", pulled_images)

        # Handle skills installation if requested
        skills_data = self.state.get("skills_setup", {})
        packages_to_install = skills_data.get("packages_to_install", []) if isinstance(skills_data, dict) else []
        installed_packages = []

        if packages_to_install:
            _setup_log(f"SetupWizard: Installing skill packages: {packages_to_install}")
            try:
                from massgen.utils.skills_installer import (
                    install_anthropic_skills,
                    install_crawl4ai_skill,
                    install_openskills_cli,
                )

                # Always need openskills CLI first for anthropic skills
                if "anthropic" in packages_to_install:
                    _setup_log("SetupWizard: Installing openskills CLI")
                    if install_openskills_cli():
                        _setup_log("SetupWizard: Installing Anthropic skills")
                        if install_anthropic_skills():
                            installed_packages.append("anthropic")

                if "crawl4ai" in packages_to_install:
                    _setup_log("SetupWizard: Installing Crawl4AI")
                    if install_crawl4ai_skill():
                        installed_packages.append("crawl4ai")

            except Exception as e:
                _setup_log(f"SetupWizard: Skills installation failed: {e}")

        self.state.set("skills_installed", installed_packages)

        return {
            "success": True,
            "configured_providers": configured_providers,
            "save_location": str(env_path.absolute()),
            "docker_images_pulled": pulled_images,
            "skills_installed": installed_packages,
        }
