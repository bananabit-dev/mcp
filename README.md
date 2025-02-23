# MCP (Model Context Protocol)

A FastAPI-based service for managing AI model interactions and web scraping capabilities.

## Features

- Image generation and manipulation using AIMLAPI
- Web scraping with ScrapeGraph
- WebSocket support for real-time updates
- CORS support for cross-origin requests

## Prerequisites

- Python 3.12+
- pip
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mcp.git
cd mcp
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your configuration:
```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000
PROJECT_NAME="Flux Pro MCP"

# CORS Configuration
BACKEND_CORS_ORIGINS=["http://localhost:8000"]

# API Configuration
AIMLAPI_KEY=your-aimlapi-key-here
SGAI_API_KEY=sgai-your-key-here

# WebSocket Configuration
WS_MESSAGE_QUEUE_SIZE=100

# Model Configuration
MAX_CONCURRENT_REQUESTS=5
REQUEST_TIMEOUT_SECONDS=300
```

## Running the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Testing Tool Configuration

Add this configuration to your `.cascade/config.json`:

```json
{
  "tools": {
    "api-test-tools": {
      "command": "curl",
      "args": [
        "-X",
        "POST",
        "-H",
        "Content-Type: application/json",
        "-d",
        "@-"
      ],
      "env": {
        "API_BASE_URL": "http://localhost:8000/api/v1"
      }
    }
  }
}
```

## Testing API Endpoints

### Image Generation
```bash
curl -X POST http://localhost:8000/api/v1/models/flux-pro-1.1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over mountains",
    "negative_prompt": "blur, haze",
    "width": 512,
    "height": 512
  }'
```

### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/scrape');
ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};
ws.send(JSON.stringify({
  query: "Search query here",
  max_results: 5
}));
```

### Web Scraping
```bash
curl -X POST http://localhost:8000/api/v1/websockets/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Search query here",
    "max_results": 5
  }'
```

## API Documentation

- OpenAPI documentation: http://localhost:8000/api/v1/docs
- ReDoc documentation: http://localhost:8000/api/v1/redoc

## Development

The project uses FastAPI with the following structure:
- `app/`: Main application directory
  - `api/`: API endpoints and routes
  - `core/`: Core configuration and settings
  - `services/`: Business logic and external service integrations
  - `schemas/`: Pydantic models and schemas

## Testing

For testing purposes, the application includes a mock ScrapeGraph service that provides simulated responses. To use the real ScrapeGraph service, update the `SCRAPEGRAPH_API_KEY` in your `.env` file with a valid key from the ScrapeGraph dashboard.

## Windsurf MCP Integration

To use this MCP server in Windsurf, follow these steps:

1. Create or edit `~/.codeium/windsurf/mcp_config.json`:
```json
{
  "mcpServers": {
    "mcp-flux": {
      "command": "python",
      "args": [
        "-m",
        "app.main"
      ],
      "cwd": "/path/to/mcp",
      "env": {
        "AIMLAPI_KEY": "your-aimlapi-key",
        "SCRAPEGRAPH_API_KEY": "your-scrapegraph-key"
      }
    }
  }
}
```

2. In Windsurf, click the hammer icon in the Cascade toolbar and click "Refresh" to load the MCP server.

3. The server provides the following tools (automatically discovered via `/mcp/tools` endpoint):
   - Image Generation (`/generate`): Generate images using text prompts
     - Args: prompt, negative_prompt, width, height
   - Image-to-Image (`/img2img`): Modify existing images using text prompts
     - Args: image, prompt, strength
   - Inpainting (`/inpaint`): Edit specific parts of images
     - Args: image, mask, prompt
   - Face Enhancement (`/enhance-face`): Improve facial features
     - Args: image
   - Upscaling (`/upscale`): Increase image resolution
     - Args: image, scale
   - Style Transfer (`/style`): Apply artistic styles to images
     - Args: image, style, strength
   - Web Scraping (`/scrape`): Extract information from websites
     - Args: url, query, max_results

4. Use these tools in Cascade by typing commands like:
```
/generate A beautiful sunset over mountains --width 512 --height 512
/scrape https://example.com "Extract product information" --max_results 5
/style path/to/image.jpg "van gogh" --strength 0.8
```

### How Tool Discovery Works

When you configure the MCP server in Windsurf, the following happens:

1. Windsurf starts the server using the command and arguments specified in `mcp_config.json`
2. The server exposes a `/mcp/tools` endpoint that returns a list of available tools and their capabilities
3. Windsurf discovers these tools and makes them available as commands in Cascade
4. You can use the tools by typing their commands (e.g., `/generate`, `/scrape`) in Cascade

You can view the available tools and their arguments at any time by:
1. Clicking the hammer icon in the Cascade toolbar
2. Clicking on the "mcp-flux" server name to expand it
3. Viewing the list of tools and their descriptions

Note: This MCP server is only available for paying individual users of Windsurf. It is not available for Teams or Enterprise users.

## Scraping Functionality

The MCP server provides a web scraping functionality that allows users to extract information from websites. The scraping functionality is powered by ScrapeGraph, a powerful web scraping API.

### Scraping Endpoints

The MCP server provides the following scraping endpoints:

* `POST /api/v1/scrape/search`: Search for content across the web
* `POST /api/v1/scrape/extract`: Extract content from a URL
* `POST /api/v1/scrape/analyze-sentiment`: Analyze the sentiment of text
* `POST /api/v1/scrape/summarize`: Summarize text

### Scraping Examples

Here are some examples of how to use the scraping endpoints:

* Search for content across the web:
```bash
curl -X POST http://localhost:8000/api/v1/scrape/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "search query",
    "max_results": 10,
    "filters": {}
  }'
```
* Extract content from a URL:
```bash
curl -X POST http://localhost:8000/api/v1/scrape/extract \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com"
  }'
```
* Analyze the sentiment of text:
```bash
curl -X POST http://localhost:8000/api/v1/scrape/analyze-sentiment \
  -H "Content-Type: application/json" \
  -d '{
    "text": "text to analyze"
  }'
```
* Summarize text:
```bash
curl -X POST http://localhost:8000/api/v1/scrape/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "text to summarize",
    "max_length": 100
  }'
```
