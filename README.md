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
```
![Cozy Kawaii Living Room](cozy_kawaii_living_room.png)
```
User: Try again with an even more cozy and kawaii living room.

Assistant: I'll enhance the kawaii and cozy elements even more in this new version!

[Generated image saved as super_cozy_kawaii_living_room.png]
```
![Super Cozy Kawaii Living Room](super_cozy_kawaii_living_room.png)


The MCP server will generate unique images each time, but they will follow the style and elements specified in the prompts. Try creating your own cozy spaces or other creative images!

### Web Scraping

The MCP server provides powerful web scraping capabilities through the ScrapeGraph API. Here are the main features:

1. **Content Extraction**
   ```python
   # Extract main content from a webpage
   result = await extract_webpage_content(
       url="https://example.com"
   )
   ```

2. **Markdown Conversion**
   ```python
   # Convert webpage to clean markdown
   result = await markdownify_webpage(
       url="https://example.com",
       clean_level="medium"  # Options: light, medium, aggressive
   )
   ```

3. **Smart Scraping**
   ```python
   # Extract specific information using AI
   result = await scrape_webpage(
       url="https://example.com"
   )
   ```

#### Features

- **AI-Powered Extraction**: Intelligently identifies and extracts main content
- **Clean Output**: Removes ads, navigation, and other clutter
- **Format Options**: Get content in raw HTML, markdown, or structured data
- **Error Handling**: Graceful fallbacks for failed extractions
- **Customization**: Control cleaning level and output format

#### Example Use Cases

1. **Documentation Generation**
   ```python
   # Create local documentation from online sources
   content = await markdownify_webpage(
       url="https://docs.example.com/guide",
       clean_level="medium"
   )
   with open(".docs/guide.md", "w") as f:
       f.write(content)
   ```

2. **Content Analysis**
   ```python
   # Extract and analyze webpage sentiment
   content = await extract_webpage_content(
       url="https://example.com/article"
   )
   sentiment = await analyze_text_sentiment(
       text=content["text"]
   )
   ```

3. **Data Collection**
   ```python
   # Extract structured data
   data = await scrape_webpage(
       url="https://example.com/products"
   )
   # Process extracted data
   for item in data["structured_data"]:
       process_item(item)
   ```

#### Best Practices

1. **Rate Limiting**
   - Respect website rate limits
   - Add delays between requests
   - Use caching when possible

2. **Error Handling**
   ```python
   try:
       content = await extract_webpage_content(url)
   except Exception as e:
       # Fall back to simpler extraction
       content = await markdownify_webpage(url)
   ```

3. **Content Cleaning**
   - Start with "medium" clean_level
   - Use "aggressive" for very noisy pages
   - Use "light" when preserving format is important

4. **Output Processing**
   - Validate extracted content
   - Handle empty or partial results
   - Process structured data appropriately

## License

MIT
