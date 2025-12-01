# FARA-7B Computer Use Tool Specification

## Tool Definition

```yaml
name: fara_computer_use
description: Execute computer automation tasks using Microsoft's FARA-7B model via Azure ML
version: 1.0.0
author: MassGen
```

## Function Signature

```python
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
) -> ExecutionResult
```

## Parameters

### Required Parameters

| Name | Type | Description |
|------|------|-------------|
| `task` | `str` | Natural language description of the task to perform |

### Optional Parameters

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `environment` | `str` | `"browser"` | Execution environment: `"browser"` or `"linux"` |
| `display_width` | `int` | `1440` | Virtual display width in pixels |
| `display_height` | `int` | `900` | Virtual display height in pixels |
| `max_iterations` | `int` | `25` | Maximum number of action iterations |
| `initial_url` | `str` | `None` | Starting URL for browser environment |
| `environment_config` | `Dict` | `None` | Environment-specific configuration |
| `agent_cwd` | `str` | `None` | Agent's current working directory |
| `model` | `str` | `"fara-7b"` | Model identifier |
| `azure_ml_endpoint` | `str` | `None` | Azure ML endpoint URL |
| `azure_ml_api_key` | `str` | `None` | Azure ML API key/token |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FARA_AZURE_ENDPOINT` | Yes* | Azure ML endpoint URL (e.g., `https://xxx.inference.ml.azure.com/score`) |
| `FARA_AZURE_API_KEY` | Yes* | Azure ML API key or bearer token |

*Required unless passed as function parameters

## Return Value

Returns `ExecutionResult` containing JSON with the following structure:

### Success Response

```json
{
    "success": true,
    "operation": "fara_computer_use",
    "task": "Original task description",
    "environment": "browser",
    "iterations": 5,
    "status": "done",
    "final_result": "Task completion description",
    "action_log": [
        {
            "iteration": 1,
            "thought": "Model's reasoning for this step",
            "action": "click(x=500, y=300)",
            "parsed_action": {
                "type": "click",
                "x": 500,
                "y": 300
            }
        }
    ]
}
```

### Failure Response

```json
{
    "success": false,
    "operation": "fara_computer_use",
    "task": "Original task description",
    "environment": "browser",
    "error": "Error description",
    "iterations": 3,
    "status": "fail",
    "failure_reason": "Reason for failure",
    "action_log": []
}
```

## Model Prompt Format

The tool sends prompts to FARA in the following format:

```
You are FARA, a Florence Agent for Rich Automation. You are asked to complete a task by interacting with a computer interface.

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
- key(key='<key>'): Press keyboard key
- scroll(direction='<dir>', amount=<int>): Scroll
- drag(start_x=<int>, start_y=<int>, end_x=<int>, end_y=<int>): Drag
- wait(seconds=<int>): Wait
- done(result='<description>'): Task completed
- fail(reason='<description>'): Task cannot be completed

Coordinate system: (0,0) is top-left, coordinates are in pixels.
Screen resolution: {width}x{height}

Task: {task}
```

## Expected Model Response Format

```
Thought: I can see the Google homepage. The search box is in the center of the page. I need to click on it to start typing my search query.

Action: click(x=512, y=305)
```

## Azure ML API Integration

### Request Format

```json
{
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "<system_prompt>"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64,<screenshot_base64>"
                    }
                }
            ]
        }
    ],
    "max_tokens": 1024,
    "temperature": 0.0
}
```

### Supported Response Formats

The client handles multiple Azure ML response formats:

1. **OpenAI-compatible**:
   ```json
   {"choices": [{"message": {"content": "..."}}]}
   ```

2. **Simple output**:
   ```json
   {"output": "..."}
   ```

3. **Response field**:
   ```json
   {"response": "..."}
   ```

4. **Generated text**:
   ```json
   {"generated_text": "..."}
   ```

5. **HuggingFace format**:
   ```json
   [{"generated_text": "..."}]
   ```

## Action Types

### Click Actions

| Action | Parsed Format | Playwright | xdotool |
|--------|--------------|------------|---------|
| `click(x=100, y=200)` | `{"type": "click", "x": 100, "y": 200}` | `page.mouse.click(100, 200)` | `xdotool mousemove 100 200 click 1` |
| `double_click(x=100, y=200)` | `{"type": "double_click", "x": 100, "y": 200}` | `page.mouse.dblclick(100, 200)` | `xdotool mousemove 100 200 click --repeat 2 1` |
| `right_click(x=100, y=200)` | `{"type": "right_click", "x": 100, "y": 200}` | `page.mouse.click(100, 200, button="right")` | `xdotool mousemove 100 200 click 3` |

### Input Actions

| Action | Parsed Format | Implementation |
|--------|--------------|----------------|
| `type(text='hello')` | `{"type": "type", "text": "hello"}` | `page.keyboard.type("hello")` |
| `key(key='Enter')` | `{"type": "key", "key": "Enter"}` | `page.keyboard.press("Enter")` |

### Navigation Actions

| Action | Parsed Format | Implementation |
|--------|--------------|----------------|
| `scroll(direction='down', amount=300)` | `{"type": "scroll", "direction": "down", "amount": 300}` | `window.scrollBy(0, 300)` |
| `drag(start_x=100, start_y=100, end_x=200, end_y=200)` | `{"type": "drag", "x1": 100, "y1": 100, "x2": 200, "y2": 200}` | Mouse down, move, up |

### Control Actions

| Action | Parsed Format | Description |
|--------|--------------|-------------|
| `wait(seconds=2)` | `{"type": "wait", "duration": 2}` | Pause execution |
| `done(result='Task completed')` | `{"type": "done", "result": "Task completed"}` | Mark task complete |
| `fail(reason='Cannot find element')` | `{"type": "fail", "reason": "Cannot find element"}` | Mark task failed |

## Usage Examples

### Example 1: Simple Web Search

```python
result = await fara_computer_use(
    task="Search for 'machine learning tutorials' on Google and click the first result",
    environment="browser",
    initial_url="https://www.google.com",
    max_iterations=10
)
```

### Example 2: Form Filling

```python
result = await fara_computer_use(
    task="Fill out the registration form with name 'John Doe', email 'john@example.com'",
    environment="browser",
    initial_url="https://example.com/register",
    display_width=1920,
    display_height=1080,
    environment_config={
        "browser_type": "chromium",
        "headless": False
    }
)
```

### Example 3: Linux Desktop Automation

```python
result = await fara_computer_use(
    task="Open the file manager and create a new folder called 'Projects'",
    environment="linux",
    environment_config={
        "container_name": "desktop-container",
        "display": ":99"
    },
    max_iterations=20
)
```

### Example 4: With Explicit Credentials

```python
result = await fara_computer_use(
    task="Navigate to dashboard and export report",
    environment="browser",
    initial_url="https://internal-app.company.com",
    azure_ml_endpoint="https://my-fara-deployment.swedencentral.inference.ml.azure.com/score",
    azure_ml_api_key="my-secret-api-key"
)
```

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `"FARA Azure ML API key not found"` | Missing API key | Set `FARA_AZURE_API_KEY` env var or pass `azure_ml_api_key` |
| `"FARA Azure ML endpoint not found"` | Missing endpoint | Set `FARA_AZURE_ENDPOINT` env var or pass `azure_ml_endpoint` |
| `"Playwright not installed"` | Missing dependency | Run `pip install playwright && playwright install` |
| `"Docker not installed"` | Missing dependency | Run `pip install docker` |
| `"Docker container not found"` | Container doesn't exist | Create the Docker container first |
| `"Failed to capture screenshot"` | Display issues | Check X11 display is running in Docker |
| `"max_iterations_reached"` | Task too complex | Increase `max_iterations` or simplify task |

### Handling Errors in Code

```python
result = await fara_computer_use(task="...")
result_data = json.loads(result.output_blocks[0].data)

if not result_data["success"]:
    if "error" in result_data:
        print(f"Error: {result_data['error']}")
    elif result_data.get("status") == "fail":
        print(f"Task failed: {result_data.get('failure_reason')}")
    elif result_data.get("status") == "max_iterations_reached":
        print("Task not completed within iteration limit")
```

## Dependencies

### Required

- `python-dotenv` - Environment variable management
- `massgen.logger_config` - Logging
- `massgen.tool._result` - Result types

### Optional (per environment)

**Browser:**
- `playwright` - Browser automation

**Linux/Docker:**
- `docker` - Docker SDK

**Async HTTP:**
- `httpx` - Async HTTP client (falls back to urllib if not available)

## Comparison with Other Computer Use Tools

| Feature | FARA | UI-TARS | Qwen | Claude |
|---------|------|---------|------|--------|
| Provider | Microsoft Azure ML | HuggingFace | Alibaba DashScope | Anthropic |
| Browser Support | ✅ | ✅ | ✅ | ✅ |
| Docker Support | ✅ | ✅ | ✅ | ✅ |
| Reasoning | ✅ | ✅ | ✅ | ✅ |
| Custom Endpoint | ✅ | ✅ | ❌ | ❌ |
| Self-hosted | ✅ | ✅ | ❌ | ❌ |
