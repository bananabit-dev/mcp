# MCP Server for Windsurf/Roocode

This is a Model Context Protocol (MCP) server that provides image generation and web scraping capabilities for Windsurf.

## Features

- **Image Generation**: Generate images using the Flux Pro model
- **Web Scraping**: Extract content from webpages using ScrapeGraph

## Getting Started

1. Clone and set up the project:
   ```bash
   git clone https://github.com/bananabit-dev/mcp.git
   cd mcp
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` to add your API keys:
   ```
   AIMLAPI_KEY=your_flux_pro_api_key
   SGAI_API_KEY=your_scrapegraph_api_key
   ```

## MCP Server Configuration

1. Add this configuration to `~/.codeium/windsurf/mcp_config.json`:
```json
{
  "mcpServers": {
    "bananabit-mcp": {
      "command": "/absolute/path/to/your/.venv/bin/python",
      "args": ["-m", "app.mcp_server"],
      "cwd": "/absolute/path/to/mcp",
      "env": {
        "PYTHONPATH": "/absolute/path/to/mcp",
        "AIMLAPI_KEY": "${env:AIMLAPI_KEY}",
        "SGAI_API_KEY": "${env:SGAI_API_KEY}"
      }
    }
  }
}
```

2. In Windsurf, click the hammer icon and "Refresh" to load the MCP server.

## Example Usage

### Image Generation

Let's create a cozy kawaii living room! Here's an example dialogue with Windsurf:

```
User: Generate a image of a cozy warm living room in kawaii and anime style.

Assistant: I'll help you generate a cozy warm living room image in kawaii and anime style!

[Generated image saved as cozy_kawaii_living_room.png]

![Cozy Kawaii Living Room](cozy_kawaii_living_room.png)

User: Try again with an even more cozy and kawaii living room.

Assistant: I'll enhance the kawaii and cozy elements even more in this new version!

[Generated image saved as super_cozy_kawaii_living_room.png]

![Super Cozy Kawaii Living Room](super_cozy_kawaii_living_room.png)
```

The MCP server will generate unique images each time, but they will follow the style and elements specified in the prompts. Try creating your own cozy spaces or other creative images!

### Web Scraping

```python
# Example tool call in Windsurf
result = await scrape_webpage(
    url="https://example.com"
)
```

## License

MIT
