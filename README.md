# Markdown to Postman Collection Converter

A Python-based MCP tool that converts structured Markdown files containing layered cURL requests into Postman Collection JSON (schema v2.1).

## ✅ What it does

- Reads a Markdown file with sections containing cURL requests
- Parses each request with metadata (description, dependencies, response variables)
- Converts cURL commands into structured Postman requests
- Builds a full Postman Collection JSON with folders, variables, and scripts
- Returns it via MCP or exports to disk

## 🧩 Core Components

| Module | Purpose |
|--------|---------|
| `markdown_parser.py` | Extracts requests + metadata from structured Markdown |
| `curl_converter.py` | Turns cURL commands → structured request objects |
| `postman_builder.py` | Creates Postman collection JSON v2.1 |
| `main.py` | Exposes commands for MCP integration |
| `simple_server.py` | Simplified server interface |
| `cli.py` | Command-line interface |

## 📝 Markdown Format

### Structure
```markdown
# Folder Name (H1 - optional, creates Postman folders)

## Request Name (H2 - required)
**Description:** Brief description of what this request does
**Requires:** comma,separated,variables (optional)
**Save Response Variable:** variable_name (optional)

  ```curl
  curl -X POST https://api.example.com/endpoint \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer {{auth_token}}" \
    -d '{"key": "value"}'
  ```
Another request...


### Supported Metadata Fields

| Field | Required? | Purpose |
|-------|----------|---------|
| **Description:** | ✅ | Request summary/documentation |
| **Requires:** | ❌ | Environment variables needed (generates pre-request scripts) |
| **Save Response Variable:** | ❌ | Variable to save from response (generates test scripts) |

### Variable Support
- Variables in cURL using `{{variable_name}}` format are automatically detected
- Creates Postman environment variables in the collection
- Pre-request scripts validate required variables exist
- Test scripts save response data to specified variables

## 🚀 Usage

### Usage as a CLI Tool

```bash
# Convert a markdown file
uv run python cli.py example.md

# With custom options
uv run python cli.py example.md -o my_collection.json --name "My API" --description "Custom description"

# Validate markdown structure only
uv run python cli.py example.md --validate --verbose

# Help
uv run python cli.py --help
```


### Usage as an MCP Server

This project exposes its conversion and validation tools as MCP (Markdown Conversion Platform) tools via [FastMCP](https://github.com/jxnl/fastmcp). You can run it as a server and use it from any MCP-compatible client.

##### 1. Setup the MCP Server

```bash
git clone <repo>
```

Add a new mcp tool to cursor

```json
// mcp config json
{
  "mcpServers": {
    "M-docs": {
      "command": "uv",
      "args": ["--directory", "<path_to_clone_of_the_project", "run", "main.py"]
    }
  }
}


```

or you can set it up as a remote server without needing to clone the repo.

```json
{
  "mcpServers": {
    "m-docs": {

      "url": "http://127.0.0.1:8000/mcp", // no deployed url yet tho .... ill update as soon as i host 
      "headers": {
        "Accept": "application/json, text/event-stream"
      }
    }
  }
}
```


This will launch the server exposing the following MCP tools:
- `convert_markdown_to_postman`: Converts a string of Markdown to Postman Collection v2.1 JSON
- `convert_markdown_file_to_postman`: Converts a Markdown file (by path) to Postman Collection v2.1 JSON
- `validate_markdown_structure`: Checks if your Markdown is correctly structured and returns validation info





## 📋 Example

### Input Markdown (`example.md`)
```markdown
# Authentication

## Login
**Description:** Get token for auth  
**Save Response Variable:** auth_token

> ```curl
> curl -X POST https://api.example.com/login \
>  -H "Content-Type: application/json" \
>  -d '{"username": "test", "password": "1234"}'
> ```

# User Operations

## Get User Profile
**Description:** Fetch user profile  
**Requires:** auth_token

> ```curl
> curl -X GET https://api.example.com/user/profile \
>  -H "Authorization: Bearer {{auth_token}}"
> ```

```
> [!NOTE]
> To avoid the markdown fenced code block breaking, we've escaped all inner code blocks with a >.

### Generated Postman Collection
- ✅ 2 folders: "Authentication" and "User Operations"
- ✅ 2 requests with proper HTTP methods, headers, and bodies
- ✅ Environment variable `auth_token` automatically detected
- ✅ Test script on Login request to save token from response
- ✅ Pre-request script on Profile request to validate token exists
- ✅ JSON body properly formatted with syntax highlighting

## 📚 Features

### ✅ Implemented Features
- [x] Metadata extraction (`**Field:**` format)
- [x] Markdown parsing with H1/H2 structure
- [x] cURL command parsing (headers, methods, body, query params)
- [x] Postman Collection v2.1 JSON generation
- [x] Folder organization
- [x] Environment variable detection and creation
- [x] Test script generation for response variable saving
- [x] Pre-request script generation for dependency checking
- [x] CLI tool with validation mode
- [x] Error handling and validation
- [x] JSON body formatting and syntax highlighting
- [] Allow dynamic markdown file generation
- [] Direct publishing to postman
- [] Allow for execution of requests within the markdown file

### 🔄 Variable Flow
1. **Detection**: `{{variable_name}}` patterns found in cURL commands
2. **Collection Variables**: Added to collection's variable array
3. **Pre-request Scripts**: Validate required variables exist
4. **Test Scripts**: Save response data to specified variables
5. **Usage**: Variables available in subsequent requests

### 🎯 MCP Integration
The tool is designed as an MCP (Model Context Protocol) tool with functions:
- `convert_markdown_to_postman()` - Convert markdown content
- `convert_file_to_postman()` - Convert markdown file
- `validate_markdown()` - Validate structure

## 📄 Output Format

Generates standard Postman Collection v2.1 JSON with:
- Collection info (name, description, schema)
- Organized folder structure
- Properly formatted requests with full URL breakdown
- Environment variables
- Event scripts (pre-request and test)
- Compatible with Postman import

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📜 License

This project is open source. See LICENSE file for details.