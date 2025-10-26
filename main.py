"""
MCP Server for Markdown to Postman Collection converter.
"""

import os
from typing import Any

from fastmcp import FastMCP

from md_to_postman.markdown_parser import MarkdownParser
from md_to_postman.postman_builder import PostmanCollectionBuilder

mcp = FastMCP("M-docs")

parser = MarkdownParser()
builder = PostmanCollectionBuilder()


@mcp.tool
def convert_markdown_to_postman(
    markdown_content: str,
    collection_name: str = "Generated Collection",
    collection_description: str = "Collection generated from Markdown",
    output_file: str | None = None,
) -> dict[str, Any]:
    """
    Convert structured Markdown with cURL requests to Postman Collection v2.1.

    Args:
        markdown_content: The markdown content containing structured cURL requests
        collection_name: Name for the generated collection
        collection_description: Description for the generated collection
        output_file: Optional file path to save the collection JSON

    Returns:
        Dict containing the Postman collection JSON and metadata
    """
    try:
        requests = parser.parse(markdown_content)

        if not requests:
            return {
                "success": False,
                "error": "No valid requests found in markdown content",
                "collection": None,
            }

        collection = builder.build_collection(
            requests, collection_name, collection_description
        )

        result = {
            "success": True,
            "collection": collection,
            "requests_count": len(requests),
            "folders_count": len(set(req.folder for req in requests if req.folder)),
            "variables_count": len(collection.get("variable", [])),
        }

        if output_file:
            builder.save_collection(collection, output_file)
            result["output_file"] = output_file

        return result

    except (OSError, ValueError, KeyError, AttributeError) as e:
        return {"success": False, "error": str(e), "collection": None}


@mcp.tool
def convert_markdown_file_to_postman(
    file_path: str,
    collection_name: str | None = None,
    collection_description: str = "Collection generated from Markdown",
    output_file: str | None = None,
) -> dict[str, Any]:
    """
    Convert a Markdown file with cURL requests to Postman Collection v2.1.

    Args:
        file_path: Path to the markdown file
        collection_name: Name for the generated collection (defaults to filename)
        collection_description: Description for the generated collection
        output_file: Optional file path to save the collection JSON

    Returns:
        Dict containing the Postman collection JSON and metadata
    """
    try:
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "collection": None,
            }

        with open(file_path, encoding="utf-8") as file:
            markdown_content = file.read()

        if collection_name is None:
            collection_name = os.path.splitext(os.path.basename(file_path))[0]

        return convert_markdown_to_postman(
            markdown_content,
            collection_name,
            collection_description,
            output_file,
        )

    except (OSError, ValueError, KeyError, AttributeError) as e:
        return {"success": False, "error": str(e), "collection": None}


@mcp.tool
def validate_markdown_structure(markdown_content: str) -> dict[str, Any]:
    """
    Validate the structure of a markdown file for conversion.

    Args:
        markdown_content: The markdown content to validate

    Returns:
        Dict containing validation results and suggestions
    """
    try:
        requests = parser.parse(markdown_content)

        validation_result = {
            "valid": True,
            "requests_found": len(requests),
            "issues": [],
            "suggestions": [],
            "requests": [],
        }

        for request in requests:
            request_info = {
                "name": request.name,
                "folder": request.folder,
                "has_description": bool(request.metadata.description),
                "has_curl": bool(request.curl_command),
                "variables_used": [],
                "issues": [],
            }

            if not request.curl_command:
                request_info["issues"].append("No cURL command found")
                validation_result["issues"].append(
                    f"Request '{request.name}': No cURL command found"
                )

            if not request.metadata.description:
                request_info["issues"].append("No description provided")
                validation_result["suggestions"].append(
                    f"Request '{request.name}': Consider adding a description"
                )

            if request.curl_command:
                variables = builder.extract_postman_variables(request.curl_command)
                request_info["variables_used"] = variables

            validation_result["requests"].append(request_info)

        if not requests:
            validation_result["valid"] = False
            validation_result["issues"].append("No valid requests found in markdown")

        return validation_result

    except (OSError, ValueError, KeyError, AttributeError) as e:
        return {
            "valid": False,
            "error": str(e),
            "requests_found": 0,
            "issues": [f"Parse error: {str(e)}"],
            "suggestions": [],
            "requests": [],
        }


if __name__ == "__main__":
    mcp.run()
