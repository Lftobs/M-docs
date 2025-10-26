"""
Postman Collection builder for creating v2.1 collection JSON.
"""

import json
import re
import shlex
import uuid
from typing import Any
from urllib.parse import parse_qs, urlparse


class PostmanCollectionBuilder:
    """Builds Postman Collection v2.1 JSON from parsed requests."""

    def __init__(self):
        # Pattern to find Postman variables {{var_name}}
        self.postman_var_pattern = re.compile(r"\{\{([^}]+)\}\}")
        self.method_flags = {"-X", "--request"}
        self.header_flags = {"-H", "--header"}
        self.data_flags = {"-d", "--data", "--data-raw", "--data-binary"}
        self.json_flags = {"--json"}

    def parse_curl_simple(self, curl_command: str) -> dict[str, Any]:
        """Simple cURL parser integrated directly."""
        curl_command = curl_command.strip()
        if curl_command.startswith("curl "):
            curl_command = curl_command[5:]

        try:
            tokens = shlex.split(curl_command)
        except ValueError:
            tokens = curl_command.split()

        method = "GET"
        url = ""
        headers = {}
        body = None

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token in self.method_flags and i + 1 < len(tokens):
                method = tokens[i + 1].upper()
                i += 2
                continue

            if token in self.header_flags and i + 1 < len(tokens):
                header_value = tokens[i + 1]
                if ":" in header_value:
                    header_name, header_val = header_value.split(":", 1)
                    headers[header_name.strip()] = header_val.strip()
                i += 2
                continue

            if token in self.data_flags and i + 1 < len(tokens):
                body = tokens[i + 1]
                if method == "GET":
                    method = "POST"
                i += 2
                continue

            if token in self.json_flags and i + 1 < len(tokens):
                body = tokens[i + 1]
                headers["Content-Type"] = "application/json"
                if method == "GET":
                    method = "POST"
                i += 2
                continue

            if token.startswith("-"):
                if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                    i += 2
                else:
                    i += 1
                continue

            if not url and not token.startswith("-"):
                url = token

            i += 1

        # parse query parameters
        query_params = {}
        if "?" in url:
            parsed_url = urlparse(url)
            query_params = {
                k: v[0] if v else "" for k, v in parse_qs(parsed_url.query).items()
            }
            url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

        return {
            "method": method,
            "url": url,
            "headers": headers,
            "body": body,
            "query_params": query_params,
        }

    def extract_postman_variables(self, text: str) -> list[str]:
        """Extract Postman variable names from text."""
        if not text:
            return []
        matches = self.postman_var_pattern.findall(text)
        return list(set(matches))

    def build_collection(
        self,
        requests: list[Any],
        collection_name: str = "Generated Collection",
        collection_description: str = "Collection generated from Markdown",
    ) -> dict[str, Any]:
        """Build a complete Postman Collection v2.1 JSON."""

        # Group requests by folder
        folders = {}
        flat_requests = []

        for parsed_request in requests:
            if hasattr(parsed_request, "folder") and parsed_request.folder:
                if parsed_request.folder not in folders:
                    folders[parsed_request.folder] = []
                folders[parsed_request.folder].append(parsed_request)
            else:
                flat_requests.append(parsed_request)

        # build collection structure
        collection = {
            "info": {
                "name": collection_name,
                "description": collection_description,
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
                "_postman_id": str(uuid.uuid4()),
                "_exporter_id": "markdown-to-postman",
            },
            "item": [],
            "variable": self._extract_all_variables(requests),
            "event": [],
        }

        # Add flat requests first
        for parsed_request in flat_requests:
            postman_request = self._convert_request(parsed_request)
            collection["item"].append(postman_request)

        # Add folder-grouped requests
        for folder_name, folder_requests in folders.items():
            folder_item = {"name": folder_name, "item": []}

            for parsed_request in folder_requests:
                postman_request = self._convert_request(parsed_request)
                folder_item["item"].append(postman_request)

            collection["item"].append(folder_item)

        return collection

    def _convert_request(self, parsed_request: Any) -> dict[str, Any]:
        """Convert a ParsedRequest to Postman request format."""
        # Parse the cURL command
        parsed_curl = self.parse_curl_simple(parsed_request.curl_command)

        # Build headers array
        headers_array = []
        for header_name, header_value in parsed_curl["headers"].items():
            headers_array.append(
                {"key": header_name, "value": header_value, "type": "text"}
            )

        # Build query parameters array
        query_array = []
        for param_name, param_value in parsed_curl["query_params"].items():
            query_array.append({"key": param_name, "value": param_value})

        # Build request body
        body = None
        if parsed_curl["body"]:
            try:
                json_data = json.loads(parsed_curl["body"])
                body = {
                    "mode": "raw",
                    "raw": json.dumps(json_data, indent=2),
                    "options": {"raw": {"language": "json"}},
                }
            except (json.JSONDecodeError, TypeError):
                body = {"mode": "raw", "raw": parsed_curl["body"]}

        parsed_url = urlparse(parsed_curl["url"])
        request = {
            "name": parsed_request.name,
            "request": {
                "method": parsed_curl["method"],
                "header": headers_array,
                "url": {
                    "raw": parsed_curl["url"]
                    + (
                        "?"
                        + "&".join(
                            f"{k}={v}" for k, v in parsed_curl["query_params"].items()
                        )
                        if parsed_curl["query_params"]
                        else ""
                    ),
                    "protocol": parsed_url.scheme or "https",
                    "host": (parsed_url.netloc or "").split(".")
                    if parsed_url.netloc
                    else [],
                    "path": (parsed_url.path or "/").strip("/").split("/")
                    if parsed_url.path and parsed_url.path != "/"
                    else [],
                    "query": query_array,
                },
            },
        }

        if body:
            request["request"]["body"] = body

        if hasattr(parsed_request, "metadata") and parsed_request.metadata.description:
            request["request"]["description"] = parsed_request.metadata.description

        # Add test script if save_response_variable is specified
        if (
            hasattr(parsed_request, "metadata")
            and parsed_request.metadata.save_response_variable
        ):
            test_script = self._generate_save_variable_script(
                parsed_request.metadata.save_response_variable
            )
            request["event"] = [
                {
                    "listen": "test",
                    "script": {"type": "text/javascript", "exec": test_script},
                }
            ]

        # Add pre-request script if requires is specified
        if hasattr(parsed_request, "metadata") and parsed_request.metadata.requires:
            prereq_script = self._generate_prereq_script(
                parsed_request.metadata.requires
            )
            if "event" not in request:
                request["event"] = []
            request["event"].append(
                {
                    "listen": "prerequest",
                    "script": {"type": "text/javascript", "exec": prereq_script},
                }
            )

        return request

    def _extract_all_variables(self, requests: list[Any]) -> list[dict[str, Any]]:
        """Extract all unique Postman variables from all requests."""
        all_variables = set()

        for parsed_request in requests:
            parsed_curl = self.parse_curl_simple(parsed_request.curl_command)

            # Check URL
            all_variables.update(self.extract_postman_variables(parsed_curl["url"]))

            # Check headers
            for header_name, header_value in parsed_curl["headers"].items():
                all_variables.update(self.extract_postman_variables(header_name))
                all_variables.update(self.extract_postman_variables(header_value))

            # Check body
            if parsed_curl["body"]:
                all_variables.update(
                    self.extract_postman_variables(parsed_curl["body"])
                )

            # Check query parameters
            for param_name, param_value in parsed_curl["query_params"].items():
                all_variables.update(self.extract_postman_variables(param_name))
                all_variables.update(self.extract_postman_variables(param_value))

            # Add variables from metadata
            if (
                hasattr(parsed_request, "metadata")
                and parsed_request.metadata.save_response_variable
            ):
                all_variables.add(parsed_request.metadata.save_response_variable)

        # Convert to Postman variable format
        postman_variables = []
        for var_name in sorted(all_variables):
            postman_variables.append({"key": var_name, "value": "", "type": "string"})

        return postman_variables

    def _generate_save_variable_script(self, variable_name: str) -> list[str]:
        """Generate test script to save response data to a variable."""
        return [
            "// Save response data to variable",
            "const responseJson = pm.response.json();",
            f"pm.environment.set('{variable_name}', responseJson.token || responseJson.access_token || responseJson.id || JSON.stringify(responseJson));",
        ]

    def _generate_prereq_script(self, required_vars: str) -> list[str]:
        """Generate pre-request script to check required variables."""
        vars_list = [var.strip() for var in required_vars.split(",")]
        script_lines = ["// Check required variables"]

        for var in vars_list:
            script_lines.extend(
                [
                    f"if (!pm.environment.get('{var}')) {{",
                    f"    throw new Error('Required variable {var} is not set');",
                    "}",
                ]
            )

        return script_lines

    def save_collection(self, collection: dict[str, Any], file_path: str) -> None:
        """Save collection to JSON file."""
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(collection, file, indent=2, ensure_ascii=False)

    def get_collection_json(self, collection: dict[str, Any]) -> str:
        """Get collection as JSON string."""
        return json.dumps(collection, indent=2, ensure_ascii=False)
