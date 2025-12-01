# -*- coding: utf-8 -*-
"""
FARA-7B Computer Use tool for automating GUI interactions using Microsoft's FARA model.

This tool implements computer control using Microsoft's FARA-7B (Florence Agent for Rich Automation) 
model deployed on Azure ML endpoints, which allows the model to:
- Control a web browser or desktop environment
- Analyze screenshots and decide actions with reasoning
- Perform multi-step workflows with thought process
- Handle desktop operations (click, type, scroll, keyboard shortcuts)
"""

import asyncio
import base64
import json
import os
import re
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from massgen.logger_config import logger
from massgen.tool._result import ExecutionResult, TextContent

# Optional dependencies with graceful fallback
try:
    from playwright.async_api import async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None

try:
    import docker

    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    docker = None

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


# Default screen dimensions
SCREEN_WIDTH = 1440
SCREEN_HEIGHT = 900

# FARA prompt templates for GUI automation
COMPUTER_USE_PROMPT = """You are FARA, a Florence Agent for Rich Automation. You are asked to complete a task by interacting with a computer interface.

You will be presented with a task and an image of the current screen state.
Your goal is to complete the task step by step through GUI interactions.

For each step:
1. First provide your reasoning in "Thought: <your reasoning>"
2. Then provide an action in "Action: <action_command>"

Available actions:
- click(x=<int>, y=<int>): Click at coordinates
- double_click(x=<int>, y=<int>): Double-click at coordinates
- right_click(x=<int>, y=<int>): Right-click at coordinates
- type(text='<text>'): Type text
- key(key='<key>'): Press keyboard key (e.g., 'Return', 'ctrl+c', 'Tab')
- scroll(direction='<dir>', amount=<int>): Scroll (up/down/left/right)
- drag(start_x=<int>, start_y=<int>, end_x=<int>, end_y=<int>): Drag from start to end
- wait(seconds=<int>): Wait for specified seconds
- done(result='<description>'): Task is completed successfully
- fail(reason='<description>'): Task cannot be completed

Coordinate system: (0,0) is top-left, coordinates are in pixels.
Screen resolution: {width}x{height}

Task: {task}
"""


def encode_image_base64(image_bytes: bytes) -> str:
    """Encode image bytes to base64 string for API calls."""
    return base64.b64encode(image_bytes).decode("utf-8")


def parse_fara_response(response: str, screen_width: int, screen_height: int) -> Dict[str, Any]:
    """Parse FARA model response into structured action.
    
    Args:
        response: Raw model response with Thought and Action
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels
        
    Returns:
        Dictionary with 'thought', 'action', and parsed action details
    """
    result = {"thought": "", "action": "", "parsed_action": None}
    
    # Extract thought and action
    thought_match = re.search(r"Thought:\s*(.+?)(?=\nAction:|$)", response, re.DOTALL)
    action_match = re.search(r"Action:\s*(.+)", response, re.DOTALL)
    
    if thought_match:
        result["thought"] = thought_match.group(1).strip()
    if action_match:
        result["action"] = action_match.group(1).strip()
    
    # Parse action into structured format
    action_text = result["action"]
    
    # Check for completion/failure
    if "done(" in action_text.lower():
        result_match = re.search(r"done\(result=['\"]([^'\"]+)['\"]", action_text, re.IGNORECASE)
        result_text = result_match.group(1) if result_match else "Task completed"
        result["parsed_action"] = {"type": "done", "result": result_text}
        return result
    if "fail(" in action_text.lower():
        reason_match = re.search(r"fail\(reason=['\"]([^'\"]+)['\"]", action_text, re.IGNORECASE)
        reason = reason_match.group(1) if reason_match else "Task failed"
        result["parsed_action"] = {"type": "fail", "reason": reason}
        return result
    if "wait(" in action_text.lower():
        seconds_match = re.search(r"wait\(seconds=(\d+)\)", action_text, re.IGNORECASE)
        seconds = int(seconds_match.group(1)) if seconds_match else 2
        result["parsed_action"] = {"type": "wait", "duration": seconds}
        return result
    
    # Parse coordinate-based actions
    if "click(" in action_text or "double_click(" in action_text or "right_click(" in action_text:
        # Extract action type
        if "double_click(" in action_text:
            action_type = "double_click"
        elif "right_click(" in action_text:
            action_type = "right_click"
        else:
            action_type = "click"
        
        # Extract coordinates
        coord_match = re.search(r"x=(\d+),\s*y=(\d+)", action_text)
        if coord_match:
            x, y = int(coord_match.group(1)), int(coord_match.group(2))
            result["parsed_action"] = {"type": action_type, "x": x, "y": y}
    
    elif "drag(" in action_text:
        # Extract start and end coordinates
        start_match = re.search(r"start_x=(\d+),\s*start_y=(\d+)", action_text)
        end_match = re.search(r"end_x=(\d+),\s*end_y=(\d+)", action_text)
        if start_match and end_match:
            x1, y1 = int(start_match.group(1)), int(start_match.group(2))
            x2, y2 = int(end_match.group(1)), int(end_match.group(2))
            result["parsed_action"] = {"type": "drag", "x1": x1, "y1": y1, "x2": x2, "y2": y2}
    
    elif "type(" in action_text:
        # Extract text to type
        text_match = re.search(r"text=['\"]([^'\"]+)['\"]", action_text)
        if text_match:
            text = text_match.group(1)
            result["parsed_action"] = {"type": "type", "text": text}
    
    elif "key(" in action_text:
        # Extract key to press
        key_match = re.search(r"key=['\"]([^'\"]+)['\"]", action_text)
        if key_match:
            key = key_match.group(1)
            result["parsed_action"] = {"type": "key", "key": key}
    
    elif "scroll(" in action_text:
        # Extract scroll direction and amount
        dir_match = re.search(r"direction=['\"]([^'\"]+)['\"]", action_text)
        amount_match = re.search(r"amount=(\d+)", action_text)
        direction = dir_match.group(1) if dir_match else "down"
        amount = int(amount_match.group(1)) if amount_match else 300
        result["parsed_action"] = {"type": "scroll", "direction": direction, "amount": amount}
    
    return result


def take_screenshot_docker(container, display: str = ":99") -> bytes:
    """Take a screenshot from Docker container using scrot.

    Args:
        container: Docker container instance
        display: X11 display number

    Returns:
        Screenshot as bytes
    """
    import time

    # Remove old screenshot if exists
    container.exec_run("rm -f /tmp/screenshot.png")

    # Take screenshot with scrot
    result = container.exec_run(
        "scrot /tmp/screenshot.png",
        environment={"DISPLAY": display},
    )

    if result.exit_code != 0:
        logger.error(f"Screenshot command failed: {result.output}")
        # Try alternative method with import
        result = container.exec_run(
            "import -window root /tmp/screenshot.png",
            environment={"DISPLAY": display},
        )
        if result.exit_code != 0:
            logger.error(f"Alternative screenshot also failed: {result.output}")
            return b""

    # Small delay to ensure file is written
    time.sleep(0.2)

    # Read the screenshot
    read_result = container.exec_run("cat /tmp/screenshot.png", stdout=True)
    if read_result.exit_code != 0:
        logger.error(f"Failed to read screenshot: {read_result.output}")
        return b""

    screenshot_bytes = read_result.output

    # Verify we got actual image data
    if len(screenshot_bytes) < 1000:
        logger.error(f"Screenshot too small ({len(screenshot_bytes)} bytes), likely invalid")
        return b""

    if not screenshot_bytes.startswith(b"\x89PNG"):
        logger.error("Screenshot does not have valid PNG header")
        return b""

    logger.info(f"Successfully captured screenshot: {len(screenshot_bytes)} bytes")
    return screenshot_bytes


async def execute_browser_action(page, action: Dict[str, Any], screen_width: int, screen_height: int) -> Dict[str, Any]:
    """Execute a browser action using Playwright.

    Args:
        page: Playwright page instance
        action: Action dictionary with type and parameters
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels

    Returns:
        Result dictionary
    """
    try:
        action_type = action.get("type")
        logger.info(f"     Executing action: {action_type}")

        if action_type == "click":
            x = action.get("x", 0)
            y = action.get("y", 0)
            await page.mouse.click(x, y)
            logger.info(f"     Clicked at ({x}, {y})")

        elif action_type == "double_click":
            x = action.get("x", 0)
            y = action.get("y", 0)
            await page.mouse.dblclick(x, y)
            logger.info(f"     Double-clicked at ({x}, {y})")

        elif action_type == "right_click":
            x = action.get("x", 0)
            y = action.get("y", 0)
            await page.mouse.click(x, y, button="right")
            logger.info(f"     Right-clicked at ({x}, {y})")

        elif action_type == "type":
            text = action.get("text", "")
            await page.keyboard.type(text)
            logger.info(f"     Typed: {text}")

        elif action_type == "key":
            key = action.get("key", "")
            await page.keyboard.press(key)
            logger.info(f"     Pressed key: {key}")

        elif action_type == "scroll":
            direction = action.get("direction", "down")
            amount = action.get("amount", 300)
            if direction == "down":
                await page.evaluate(f"window.scrollBy(0, {amount})")
            elif direction == "up":
                await page.evaluate(f"window.scrollBy(0, -{amount})")
            elif direction == "left":
                await page.evaluate(f"window.scrollBy(-{amount}, 0)")
            elif direction == "right":
                await page.evaluate(f"window.scrollBy({amount}, 0)")
            logger.info(f"     Scrolled {direction} by {amount}px")

        elif action_type == "drag":
            x1 = action.get("x1", 0)
            y1 = action.get("y1", 0)
            x2 = action.get("x2", 0)
            y2 = action.get("y2", 0)
            await page.mouse.move(x1, y1)
            await page.mouse.down()
            await page.mouse.move(x2, y2)
            await page.mouse.up()
            logger.info(f"     Dragged from ({x1}, {y1}) to ({x2}, {y2})")

        elif action_type == "wait":
            duration = action.get("duration", 1)
            await asyncio.sleep(duration)
            logger.info(f"     Waited {duration} seconds")

        elif action_type in ["done", "fail"]:
            logger.info(f"     Task {action_type}")
            return {"success": True, "completed": True, "status": action_type}

        else:
            logger.warning(f"     Unknown action type: {action_type}")
            return {"error": f"Unknown action type: {action_type}"}

        # Wait for potential navigations/renders
        try:
            await page.wait_for_load_state(timeout=2000)
        except Exception:
            pass

        await asyncio.sleep(0.5)

        return {"success": True}

    except Exception as e:
        logger.error(f"Error executing action {action.get('type')}: {e}")
        return {"error": str(e)}


def execute_docker_action(container, action: Dict[str, Any], screen_width: int, screen_height: int, display: str = ":99") -> Dict[str, Any]:
    """Execute an action in Docker using xdotool.

    Args:
        container: Docker container instance
        action: Action dictionary with type and parameters
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels
        display: X11 display number

    Returns:
        Result dictionary
    """
    import time

    try:
        action_type = action.get("type")
        logger.info(f"     Docker executing action: {action_type}")

        if action_type == "click":
            x = action.get("x", 0)
            y = action.get("y", 0)
            container.exec_run(
                f"xdotool mousemove {x} {y} click 1",
                environment={"DISPLAY": display},
            )
            logger.info(f"     Docker clicked at ({x}, {y})")

        elif action_type == "double_click":
            x = action.get("x", 0)
            y = action.get("y", 0)
            container.exec_run(
                f"xdotool mousemove {x} {y} click --repeat 2 1",
                environment={"DISPLAY": display},
            )
            logger.info(f"     Docker double-clicked at ({x}, {y})")

        elif action_type == "right_click":
            x = action.get("x", 0)
            y = action.get("y", 0)
            container.exec_run(
                f"xdotool mousemove {x} {y} click 3",
                environment={"DISPLAY": display},
            )
            logger.info(f"     Docker right-clicked at ({x}, {y})")

        elif action_type == "type":
            text = action.get("text", "")
            escaped_text = text.replace("'", "'\\''")
            container.exec_run(
                f"xdotool type '{escaped_text}'",
                environment={"DISPLAY": display},
            )
            logger.info(f"     Docker typed: {text}")

        elif action_type == "key":
            key = action.get("key", "")
            # Convert key format
            xdotool_key = key.replace("Control", "ctrl").replace("Shift", "shift").replace("Alt", "alt")
            container.exec_run(
                f"xdotool key {xdotool_key}",
                environment={"DISPLAY": display},
            )
            logger.info(f"     Docker pressed key: {key}")

        elif action_type == "scroll":
            direction = action.get("direction", "down")
            if direction == "down":
                cmd = "xdotool key Page_Down"
            elif direction == "up":
                cmd = "xdotool key Page_Up"
            elif direction == "left":
                cmd = "xdotool key Left Left Left"
            elif direction == "right":
                cmd = "xdotool key Right Right Right"
            else:
                cmd = "xdotool key Page_Down"
            container.exec_run(cmd, environment={"DISPLAY": display})
            logger.info(f"     Docker scrolled {direction}")

        elif action_type == "drag":
            x1 = action.get("x1", 0)
            y1 = action.get("y1", 0)
            x2 = action.get("x2", 0)
            y2 = action.get("y2", 0)
            container.exec_run(
                f"xdotool mousemove {x1} {y1} mousedown 1 mousemove {x2} {y2} mouseup 1",
                environment={"DISPLAY": display},
            )
            logger.info(f"     Docker dragged from ({x1}, {y1}) to ({x2}, {y2})")

        elif action_type == "wait":
            duration = action.get("duration", 1)
            time.sleep(duration)
            logger.info(f"     Docker waited {duration} seconds")

        elif action_type in ["done", "fail"]:
            logger.info(f"     Task {action_type}")
            return {"success": True, "completed": True, "status": action_type}

        else:
            logger.warning(f"     Unknown action type: {action_type}")
            return {"error": f"Unknown action type: {action_type}"}

        time.sleep(0.5)
        return {"success": True}

    except Exception as e:
        logger.error(f"Error executing Docker action {action.get('type')}: {e}")
        return {"error": str(e)}


class FaraAzureMLClient:
    """Client for calling FARA-7B model via Azure ML endpoint."""
    
    def __init__(self, endpoint_url: str, api_key: str, timeout: int = 60):
        """Initialize the Azure ML client.
        
        Args:
            endpoint_url: Azure ML endpoint URL (e.g., https://xxx.inference.ml.azure.com/score)
            api_key: Azure ML API key or token
            timeout: Request timeout in seconds
        """
        self.endpoint_url = endpoint_url
        self.api_key = api_key
        self.timeout = timeout
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
    
    def call_model(self, messages: List[Dict[str, Any]], max_tokens: int = 1024, temperature: float = 0.0) -> str:
        """Call the FARA model with messages.
        
        Args:
            messages: List of message dictionaries (role + content)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
        Returns:
            Model response text
        """
        # Build request payload for Azure ML
        # The format depends on how the model is deployed
        data = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        body = json.dumps(data).encode('utf-8')
        
        req = urllib.request.Request(self.endpoint_url, body, self.headers)
        
        try:
            response = urllib.request.urlopen(req, timeout=self.timeout)
            result = response.read().decode('utf-8')
            
            # Parse response - format depends on Azure ML deployment
            try:
                result_json = json.loads(result)
                # Try common response formats
                if isinstance(result_json, dict):
                    if "choices" in result_json:
                        # OpenAI-like format
                        return result_json["choices"][0]["message"]["content"]
                    elif "output" in result_json:
                        return result_json["output"]
                    elif "response" in result_json:
                        return result_json["response"]
                    elif "result" in result_json:
                        return result_json["result"]
                    elif "text" in result_json:
                        return result_json["text"]
                    elif "generated_text" in result_json:
                        return result_json["generated_text"]
                    else:
                        # Return full JSON as string if unknown format
                        return json.dumps(result_json)
                elif isinstance(result_json, list) and len(result_json) > 0:
                    # List response
                    if isinstance(result_json[0], dict):
                        if "generated_text" in result_json[0]:
                            return result_json[0]["generated_text"]
                    return json.dumps(result_json)
                else:
                    return str(result_json)
            except json.JSONDecodeError:
                return result
                
        except urllib.error.HTTPError as error:
            error_msg = f"Azure ML request failed with status {error.code}: {error.read().decode('utf8', 'ignore')}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except urllib.error.URLError as error:
            error_msg = f"Azure ML connection failed: {error.reason}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def call_model_async(self, messages: List[Dict[str, Any]], max_tokens: int = 1024, temperature: float = 0.0) -> str:
        """Async version of call_model using httpx if available, otherwise falls back to sync.
        
        Args:
            messages: List of message dictionaries (role + content)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
        Returns:
            Model response text
        """
        if HTTPX_AVAILABLE:
            data = {
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.endpoint_url,
                    json=data,
                    headers=self.headers
                )
                response.raise_for_status()
                result = response.text
                
                try:
                    result_json = json.loads(result)
                    if isinstance(result_json, dict):
                        if "choices" in result_json:
                            return result_json["choices"][0]["message"]["content"]
                        elif "output" in result_json:
                            return result_json["output"]
                        elif "response" in result_json:
                            return result_json["response"]
                        elif "result" in result_json:
                            return result_json["result"]
                        elif "text" in result_json:
                            return result_json["text"]
                        elif "generated_text" in result_json:
                            return result_json["generated_text"]
                        else:
                            return json.dumps(result_json)
                    elif isinstance(result_json, list) and len(result_json) > 0:
                        if isinstance(result_json[0], dict) and "generated_text" in result_json[0]:
                            return result_json[0]["generated_text"]
                        return json.dumps(result_json)
                    else:
                        return str(result_json)
                except json.JSONDecodeError:
                    return result
        else:
            # Fall back to sync call in executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self.call_model(messages, max_tokens, temperature)
            )


async def fara_computer_use(
    task: str,
    environment: str = "browser",
    display_width: int = 1440,
    display_height: int = 900,
    max_iterations: int = 25,
    initial_url: Optional[str] = None,
    environment_config: Optional[Dict[str, Any]] = None,
    agent_cwd: Optional[str] = None,
    model: str = "fara-7b",
    azure_ml_endpoint: Optional[str] = None,
    azure_ml_api_key: Optional[str] = None,
) -> ExecutionResult:
    """
    Execute a computer automation task using Microsoft's FARA-7B model via Azure ML.

    This tool implements GUI control using Microsoft's FARA (Florence Agent for Rich Automation)
    model deployed on Azure ML, which analyzes screenshots and generates actions with reasoning 
    to autonomously control a browser or Linux desktop.

    Args:
        task: Description of the task to perform
        environment: Environment type - "browser" or "linux" (Docker)
        display_width: Display width in pixels (default: 1440)
        display_height: Display height in pixels (default: 900)
        max_iterations: Maximum number of action iterations (default: 25)
        initial_url: Initial URL to navigate to (browser only)
        environment_config: Additional configuration (browser: headless/browser_type, docker: container_name/display)
        agent_cwd: Agent's current working directory
        model: Model name (default: fara-7b)
        azure_ml_endpoint: Azure ML endpoint URL (or set FARA_AZURE_ENDPOINT env var)
        azure_ml_api_key: Azure ML API key (or set FARA_AZURE_API_KEY env var)

    Returns:
        ExecutionResult containing success status, action log with thoughts, and results

    Examples:
        # Browser task
        fara_computer_use(
            "Search for Python documentation on Google",
            environment="browser",
            azure_ml_endpoint="https://xxx.inference.ml.azure.com/score",
            azure_ml_api_key="your-api-key"
        )

        # Docker task
        fara_computer_use(
            "Open Firefox and browse to GitHub",
            environment="linux",
            environment_config={"container_name": "cua-container", "display": ":99"},
            azure_ml_endpoint="https://xxx.inference.ml.azure.com/score"
        )

    Prerequisites:
        - FARA_AZURE_API_KEY environment variable or azure_ml_api_key parameter
        - FARA_AZURE_ENDPOINT environment variable or azure_ml_endpoint parameter
        - For browser: pip install playwright && playwright install
        - For Docker: Docker container with X11 and xdotool installed
        - Optional: pip install httpx (for async HTTP requests)
    """
    # Check environment-specific dependencies
    if environment == "linux":
        if not DOCKER_AVAILABLE:
            result = {
                "success": False,
                "operation": "fara_computer_use",
                "error": "Docker not installed. Install with: pip install docker",
            }
            return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])
    else:  # browser
        if not PLAYWRIGHT_AVAILABLE:
            result = {
                "success": False,
                "operation": "fara_computer_use",
                "error": "Playwright not installed. Install with: pip install playwright && playwright install",
            }
            return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])

    environment_config = environment_config or {}

    try:
        # Load environment variables
        script_dir = Path(__file__).parent.parent.parent.parent
        env_path = script_dir / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()

        # Get API credentials
        api_key = azure_ml_api_key or os.getenv("FARA_AZURE_API_KEY")
        if not api_key:
            result = {
                "success": False,
                "operation": "fara_computer_use",
                "error": "FARA Azure ML API key not found. Set FARA_AZURE_API_KEY in .env or pass azure_ml_api_key parameter.",
            }
            return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])

        # Get endpoint URL
        endpoint = azure_ml_endpoint or os.getenv("FARA_AZURE_ENDPOINT")
        if not endpoint:
            result = {
                "success": False,
                "operation": "fara_computer_use",
                "error": "FARA Azure ML endpoint not found. Set FARA_AZURE_ENDPOINT in .env or pass azure_ml_endpoint parameter.",
            }
            return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])

        # Initialize FARA client
        client = FaraAzureMLClient(
            endpoint_url=endpoint,
            api_key=api_key,
            timeout=120
        )

        # Initialize environment (browser or Docker)
        container = None
        display = None
        page = None
        playwright_instance = None
        browser = None

        if environment == "linux":
            # Docker environment
            logger.info("Initializing Docker environment...")
            container_name = environment_config.get("container_name", "cua-container")
            display = environment_config.get("display", ":99")

            docker_client = docker.from_env()
            try:
                container = docker_client.containers.get(container_name)
                if container.status != "running":
                    logger.info(f"Starting container {container_name}...")
                    container.start()
                logger.info(f"Using Docker container: {container_name} (display {display})")
            except docker.errors.NotFound:
                result = {
                    "success": False,
                    "operation": "fara_computer_use",
                    "error": f"Docker container '{container_name}' not found. Please create it first.",
                }
                return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])

            # Take initial screenshot from Docker
            initial_screenshot = take_screenshot_docker(container, display)

            if not initial_screenshot or len(initial_screenshot) < 1000:
                result = {
                    "success": False,
                    "operation": "fara_computer_use",
                    "error": f"Failed to capture screenshot from Docker. Check X11 display {display} is running.",
                }
                return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])

        else:  # browser
            # Browser environment
            logger.info("Initializing browser environment...")
            playwright_instance = await async_playwright().start()
            
            browser_type_name = environment_config.get("browser_type", "chromium")
            headless = environment_config.get("headless", False)
            
            if browser_type_name == "firefox":
                browser = await playwright_instance.firefox.launch(headless=headless)
            elif browser_type_name == "webkit":
                browser = await playwright_instance.webkit.launch(headless=headless)
            else:
                browser = await playwright_instance.chromium.launch(headless=headless)

            context = await browser.new_context(
                viewport={"width": display_width, "height": display_height},
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            )
            page = await context.new_page()

            # Navigate to initial URL
            if initial_url:
                await page.goto(initial_url, wait_until="networkidle", timeout=30000)
            else:
                await page.goto("about:blank")

            await asyncio.sleep(1)
            initial_screenshot = await page.screenshot()

        # Build system prompt
        system_prompt = COMPUTER_USE_PROMPT.format(
            width=display_width,
            height=display_height,
            task=task
        )

        # Initialize conversation history
        messages = []
        action_log = []
        iteration = 0

        logger.info(f"Starting FARA automation: {task}")
        logger.info(f"Environment: {environment}, Resolution: {display_width}x{display_height}")

        # Main interaction loop
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"\n=== Iteration {iteration}/{max_iterations} ===")

            # Take screenshot
            if environment == "linux":
                screenshot_bytes = take_screenshot_docker(container, display)
            else:
                screenshot_bytes = await page.screenshot()

            if not screenshot_bytes:
                logger.error("Failed to capture screenshot")
                break

            # Encode screenshot
            screenshot_base64 = encode_image_base64(screenshot_bytes)

            # Build message for FARA
            if iteration == 1:
                # First message includes task
                user_message = {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": system_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{screenshot_base64}"},
                        },
                    ],
                }
            else:
                # Subsequent messages just have screenshot
                user_message = {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Here is the current screenshot. Continue with the task."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{screenshot_base64}"},
                        },
                    ],
                }

            messages.append(user_message)

            # Call FARA API
            try:
                logger.info("Calling FARA Azure ML API...")
                
                response_text = await client.call_model_async(
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.0
                )

                logger.info(f"FARA response:\n{response_text}")

                # Add assistant response to history
                messages.append({"role": "assistant", "content": response_text})

                # Parse response
                parsed = parse_fara_response(response_text, display_width, display_height)
                
                thought = parsed.get("thought", "")
                action_text = parsed.get("action", "")
                parsed_action = parsed.get("parsed_action")

                action_log.append({
                    "iteration": iteration,
                    "thought": thought,
                    "action": action_text,
                    "parsed_action": parsed_action,
                })

                logger.info(f"Thought: {thought}")
                logger.info(f"Action: {action_text}")

                # Check if task is completed or failed
                if parsed_action and parsed_action.get("type") in ["done", "fail"]:
                    status = parsed_action["type"]
                    logger.info(f"Task {status}!")
                    
                    result = {
                        "success": status == "done",
                        "operation": "fara_computer_use",
                        "task": task,
                        "environment": environment,
                        "iterations": iteration,
                        "status": status,
                        "action_log": action_log,
                    }
                    
                    if status == "done":
                        result["final_result"] = parsed_action.get("result", "Task completed")
                    else:
                        result["failure_reason"] = parsed_action.get("reason", "Task failed")
                    
                    # Clean up
                    if browser:
                        await browser.close()
                    if playwright_instance:
                        await playwright_instance.stop()
                    
                    return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])

                # Execute action
                if parsed_action:
                    if environment == "linux":
                        exec_result = execute_docker_action(
                            container, parsed_action, display_width, display_height, display
                        )
                    else:
                        exec_result = await execute_browser_action(
                            page, parsed_action, display_width, display_height
                        )

                    if exec_result.get("error"):
                        logger.error(f"Action execution error: {exec_result['error']}")
                    elif exec_result.get("completed"):
                        # Task completed
                        result = {
                            "success": True,
                            "operation": "fara_computer_use",
                            "task": task,
                            "environment": environment,
                            "iterations": iteration,
                            "status": exec_result.get("status", "done"),
                            "action_log": action_log,
                        }
                        
                        # Clean up
                        if browser:
                            await browser.close()
                        if playwright_instance:
                            await playwright_instance.stop()
                        
                        return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])
                else:
                    logger.warning("No valid action parsed from response")

            except Exception as e:
                logger.error(f"Error in iteration {iteration}: {e}")
                action_log.append({
                    "iteration": iteration,
                    "error": str(e),
                })

        # Max iterations reached
        logger.info("Max iterations reached")
        result = {
            "success": False,
            "operation": "fara_computer_use",
            "task": task,
            "environment": environment,
            "iterations": iteration,
            "status": "max_iterations_reached",
            "action_log": action_log,
        }

        # Clean up
        if browser:
            await browser.close()
        if playwright_instance:
            await playwright_instance.stop()

        return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])

    except Exception as e:
        error_msg = f"FARA computer use failed: {e}"
        logger.error(error_msg)
        result = {
            "success": False,
            "operation": "fara_computer_use",
            "error": error_msg,
            "task": task,
            "environment": environment,
        }
        
        # Clean up on error
        try:
            if browser:
                await browser.close()
            if playwright_instance:
                await playwright_instance.stop()
        except:
            pass
        
        return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])
