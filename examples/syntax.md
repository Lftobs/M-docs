# Supported Markdown Syntax

This document outlines the markdown syntax supported by the m-docs converter for converting structured markdown files containing cURL requests into Postman Collections.

## Syntax mapping details

- Folder Headers (H1)
  
  - **Usage**: # Folder Name
  - **Purpose**: It is use to group route logic eg all Auth route which is then used later to create a postman folder
  - **Optional**: Requests without a preceding H1 header will be placed at the root level
  - **Example**: `# Authentication`, `# User Operations`

- Request Name (H2)

  - **Usage**: ## Request Name
  - **Purpose**: Defines individual API requests
  - **Required**: Each request must have an H2 header
  - **Example**: `## Login`, `## Get User Profile`

- Request Metadata

All metadata fields use the `**Field Name:** value` format and are placed directly after the request header.

  - **Usage**: **Description:** Brief description of what this request does
  - **Required**: Yes (recommended for documentation)
  - **Purpose**: Provides documentation for the request in Postman
  - **Example**: `**Description:** Get authentication token for API access`
  - **Supported metadata**: `Requires`, `Description` and  `Save Response Variable`

- Requires Field
 
  - **Usage**: **Requires:** variable1,variable2,variable3
  - **Optional**: Yes
  - **Purpose**: Specifies environment variables that must be set before the request runs
  - **Format**: Comma-separated variable names (no spaces around commas)
  - **Generates**: Pre-request script that validates required variables exist
  - **Example**: `**Requires:** auth_token,user_id`

- Save Response Variable Field
  -**Usage**: **Save Response Variable:** variable_name
  - **Optional**: Yes
  - **Purpose**: Extracts data from the response and saves it to an environment variable
  - **Generates**: Test script that saves response data
  - **Auto-detection**: Attempts to save `token`, `access_token`, `id`, or the entire response as JSON
  - **Example**: `**Save Response Variable:** auth_token`

- cURL Code Blocks

  - **Usage**: ```curl
curl -X METHOD https://api.example.com/endpoint \
  -H "Header-Name: header-value" \
  -d '{"key": "value"}'
```
````markdown

````

### Supported cURL Options

#### HTTP Methods
- **Flags**: `-X`, `--request`
- **Supported**: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- **Default**: GET (changes to POST if data is provided)
- **Example**: `curl -X POST https://api.example.com/login`

#### Headers
- **Flags**: `-H`, `--header`
- **Format**: `"Header-Name: header-value"`
- **Multiple**: Supported (use multiple `-H` flags)
- **Example**: `-H "Content-Type: application/json" -H "Authorization: Bearer {{token}}"`

#### Request Body
- **Data Flags**: `-d`, `--data`, `--data-raw`, `--data-binary`
- **JSON Flag**: `--json` (automatically sets Content-Type to application/json)
- **JSON Detection**: Automatically formats valid JSON with syntax highlighting
- **Raw Text**: Non-JSON data is treated as raw text
- **Example**: `-d '{"username": "test", "password": "1234"}'`

#### Query Parameters
- **Format**: Included in the URL after `?`
- **Parsing**: Automatically extracted from URL
- **Multiple**: Supported with `&` separator
- **Example**: `https://api.example.com/users?page=1&limit=10`

## Variable System

### Postman Variables
- **Format**: `{{variable_name}}`
- **Usage**: Can be used in URLs, headers, body, and query parameters
- **Auto-detection**: All variables are automatically detected and added to collection
- **Example**: `{{auth_token}}`, `{{base_url}}`, `{{user_id}}`

### Variable Flow
1. **Detection**: Variables in `{{}}` format are found in cURL commands
2. **Collection Variables**: Added to the collection's variable array
3. **Pre-request Scripts**: Generated to validate required variables exist
4. **Test Scripts**: Generated to save response data to specified variables
5. **Usage**: Variables become available for subsequent requests


## Generated Output based on example.md

The above example generates:
- **2 folders**: "Authentication" and "User Management"
- **3 requests** with proper HTTP methods, headers, and bodies
- **Environment variables**: `username`, `password`, `auth_token`, `user_name`, `user_email`
- **Pre-request script** on profile requests to validate `auth_token` exists
- **Test script** on login request to save authentication token
- **JSON formatting** with syntax highlighting for request bodies

## Validation Rules

1. **Required Elements**:
   - At least one H2 header (request name)
   - At least one cURL code block per request

2. **Optional Elements**:
   - H1 headers (folders)
   - Metadata fields
   - Variables

3. **Best Practices**:
   - Always include descriptions for documentation
   - Use meaningful variable names
   - Group related requests under folders
   - Specify required variables for dependent requests
