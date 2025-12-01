# FARA Computer Use Tool

This tool implements computer automation using Microsoft's **FARA-7B** (Florence Agent for Rich Automation) model deployed on Azure ML endpoints.

## Overview

FARA (Florence Agent for Rich Automation) is Microsoft's vision-language model designed for GUI automation tasks. This tool allows autonomous control of:

- **Web Browsers** - Using Playwright for precise control
- **Linux Desktops** - Using Docker containers with X11 and xdotool

## Features

- **Screenshot Analysis**: FARA analyzes screen state to understand UI elements
- **Reasoning with Actions**: Each step includes thought process explaining the reasoning
- **Multi-step Workflows**: Automatically chains multiple actions to complete complex tasks
- **Browser & Desktop Support**: Works with both browser automation and Linux desktop environments
- **Azure ML Integration**: Native support for Azure Machine Learning endpoints

## Prerequisites

### Required

1. **Azure ML Endpoint**: FARA-7B model deployed on Azure ML
2. **API Key**: Azure ML endpoint key or token
3. **Python packages**:
   ```bash
   pip install python-dotenv
   ```

### For Browser Automation

```bash
pip install playwright
playwright install chromium  # or firefox, webkit
```

### For Docker/Linux Desktop

```bash
pip install docker
```

A Docker container with X11 display (Xvfb), scrot, and xdotool installed.

### Optional

```bash
pip install httpx  # For async HTTP requests
```

## Configuration

Set environment variables in `.env` file or system environment:

```env
# Required
FARA_AZURE_ENDPOINT=https://your-endpoint.inference.ml.azure.com/score
FARA_AZURE_API_KEY=your-api-key-or-token
```

Or pass directly to the function:

```python
fara_computer_use(
    task="...",
    azure_ml_endpoint="https://your-endpoint.inference.ml.azure.com/score",
    azure_ml_api_key="your-api-key"
)
```

## Usage

### Basic Browser Task

```python
import asyncio
from massgen.tool._fara_computer_use import fara_computer_use

async def main():
    result = await fara_computer_use(
        task="Search for 'Python documentation' on Google",
        environment="browser",
        initial_url="https://www.google.com"
    )
    print(result)

asyncio.run(main())
```

### Browser with Custom Settings

```python
result = await fara_computer_use(
    task="Fill out the contact form with test data",
    environment="browser",
    display_width=1920,
    display_height=1080,
    max_iterations=30,
    initial_url="https://example.com/contact",
    environment_config={
        "browser_type": "chromium",  # chromium, firefox, webkit
        "headless": False  # Show browser window
    }
)
```

### Docker/Linux Desktop Task

```python
result = await fara_computer_use(
    task="Open Firefox and navigate to GitHub",
    environment="linux",
    environment_config={
        "container_name": "cua-container",
        "display": ":99"
    }
)
```

## API Reference

### `fara_computer_use()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `task` | str | *required* | Description of the task to perform |
| `environment` | str | "browser" | "browser" or "linux" |
| `display_width` | int | 1440 | Screen width in pixels |
| `display_height` | int | 900 | Screen height in pixels |
| `max_iterations` | int | 25 | Maximum action iterations |
| `initial_url` | str | None | Initial URL (browser only) |
| `environment_config` | dict | None | Environment-specific config |
| `agent_cwd` | str | None | Agent working directory |
| `model` | str | "fara-7b" | Model identifier |
| `azure_ml_endpoint` | str | None | Azure ML endpoint URL |
| `azure_ml_api_key` | str | None | Azure ML API key |

### Environment Config Options

**Browser:**
```python
{
    "browser_type": "chromium",  # chromium, firefox, webkit
    "headless": False  # True for headless mode
}
```

**Linux/Docker:**
```python
{
    "container_name": "cua-container",  # Docker container name
    "display": ":99"  # X11 display number
}
```

## Available Actions

FARA can generate the following actions:

| Action | Format | Description |
|--------|--------|-------------|
| click | `click(x=<int>, y=<int>)` | Left-click at coordinates |
| double_click | `double_click(x=<int>, y=<int>)` | Double-click at coordinates |
| right_click | `right_click(x=<int>, y=<int>)` | Right-click at coordinates |
| type | `type(text='<text>')` | Type text |
| key | `key(key='<key>')` | Press keyboard key |
| scroll | `scroll(direction='<dir>', amount=<int>)` | Scroll in direction |
| drag | `drag(start_x=<int>, start_y=<int>, end_x=<int>, end_y=<int>)` | Drag operation |
| wait | `wait(seconds=<int>)` | Wait for duration |
| done | `done(result='<description>')` | Task completed |
| fail | `fail(reason='<description>')` | Task failed |

## Response Format

The tool returns an `ExecutionResult` containing JSON with:

```json
{
    "success": true,
    "operation": "fara_computer_use",
    "task": "Search for Python documentation",
    "environment": "browser",
    "iterations": 5,
    "status": "done",
    "final_result": "Successfully searched and found Python documentation",
    "action_log": [
        {
            "iteration": 1,
            "thought": "I need to click on the search box...",
            "action": "click(x=500, y=300)",
            "parsed_action": {"type": "click", "x": 500, "y": 300}
        }
    ]
}
```

## Azure ML Endpoint Setup

1. Deploy FARA-7B model on Azure ML:
   - Create Azure ML workspace
   - Deploy model as managed online endpoint
   - Note the endpoint URL and key

2. Expected endpoint request format:
   ```json
   {
       "messages": [
           {
               "role": "user",
               "content": [
                   {"type": "text", "text": "..."},
                   {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
               ]
           }
       ],
       "max_tokens": 1024,
       "temperature": 0.0
   }
   ```

3. Expected response format (supports multiple formats):
   - OpenAI-like: `{"choices": [{"message": {"content": "..."}}]}`
   - Simple: `{"output": "..."}` or `{"response": "..."}`

## Troubleshooting

### Common Issues

1. **"API key not found"**
   - Ensure `FARA_AZURE_API_KEY` is set in environment or passed as parameter

2. **"Endpoint not found"**
   - Ensure `FARA_AZURE_ENDPOINT` is set correctly
   - Verify endpoint URL ends with `/score`

3. **"Failed to capture screenshot"**
   - For browser: Ensure Playwright is installed
   - For Docker: Check X11 display is running

4. **"No valid action parsed"**
   - Model response format may differ; check logs for raw response

### Debug Mode

Enable verbose logging:

```python
import logging
logging.getLogger("massgen").setLevel(logging.DEBUG)
```

## Related Tools

- [UI-TARS Computer Use](../_ui_tars_computer_use/) - ByteDance's UI-TARS model
- [Qwen Computer Use](../_qwen_computer_use/) - Alibaba's Qwen VL model
- [Claude Computer Use](../_claude_computer_use/) - Anthropic's Claude model
- [Gemini Computer Use](../_gemini_computer_use/) - Google's Gemini model

## License

Part of the MassGen project.
