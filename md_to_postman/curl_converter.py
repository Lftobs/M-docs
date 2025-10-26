"""
cURL command parser and converter to structured request format.
"""

import json
import re
import shlex
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlparse


@dataclass
class ParsedCurl:
    """Structured representation of a parsed cURL command."""

    method: str
    url: str
    headers: dict[str, str]
    body: str | None = None
    query_params: dict[str, str] | None = None

    def __post_init__(self):
        if self.query_params is None:
            self.query_params = {}


class CurlConverter:
    """Converts cURL commands to structured request objects."""

    def __init__(self):
        self.method_flags = {"-X", "--request"}
        self.header_flags = {"-H", "--header"}
        self.data_flags = {"-d", "--data", "--data-raw", "--data-binary"}
        self.json_flags = {"--json"}

        # Pattern to find Postman variables {{var_name}}
        self.postman_var_pattern = re.compile(r"\{\{([^}]+)\}\}")

    def parse_curl(self, curl_command: str) -> ParsedCurl:
        """Parse a cURL command string into structured components."""
        curl_command = curl_command.strip()
        if curl_command.startswith("curl "):
            curl_command = curl_command[5:]

        # Split the command into tokens using shlex to handle quotes properly
        try:
            tokens = shlex.split(curl_command)
        except ValueError:
            tokens = curl_command.split()

        method = "GET"  # Default method
        url = ""
        headers = {}
        body = None

        i = 0
        while i < len(tokens):
            token = tokens[i]

            # get method flag
            if token in self.method_flags and i + 1 < len(tokens):
                method = tokens[i + 1].upper()
                i += 2
                continue

            # get header flag
            if token in self.header_flags and i + 1 < len(tokens):
                header_value = tokens[i + 1]
                if ":" in header_value:
                    header_name, header_val = header_value.split(":", 1)
                    headers[header_name.strip()] = header_val.strip()
                i += 2
                continue

            # get data flag
            if token in self.data_flags and i + 1 < len(tokens):
                body = tokens[i + 1]
                if method == "GET":  # If data is provided but no method, assume POST
                    method = "POST"
                i += 2
                continue

            # get JSON flag
            if token in self.json_flags and i + 1 < len(tokens):
                body = tokens[i + 1]
                headers["Content-Type"] = "application/json"
                if method == "GET":
                    method = "POST"
                i += 2
                continue

            # skip other flags we don't handle fn
            if token.startswith("-"):
                # Try to skip flag and its value if it has one
                if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                    i += 2
                else:
                    i += 1
                continue

            # check for the URL
            if not url and not token.startswith("-"):
                url = token

            i += 1

        # parse query parameters from URL
        query_params = {}
        if "?" in url:
            parsed_url = urlparse(url)
            query_params = {
                k: v[0] if v else "" for k, v in parse_qs(parsed_url.query).items()
            }

            url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

        return ParsedCurl(
            method=method,
            url=url,
            headers=headers,
            body=body,
            query_params=query_params,
        )

    def extract_postman_variables(self, text: str) -> list[str]:
        """Extract Postman variable names from text."""
        if not text:
            return []

        matches = self.postman_var_pattern.findall(text)
        return list(set(matches))

    def get_all_variables(self, parsed_curl: ParsedCurl) -> list[str]:
        """Get all Postman variables used in the request."""
        variables = []

        # check url
        variables.extend(self.extract_postman_variables(parsed_curl.url))

        # check headers
        for header_name, header_value in parsed_curl.headers.items():
            variables.extend(self.extract_postman_variables(header_name))
            variables.extend(self.extract_postman_variables(header_value))

        # check body
        if parsed_curl.body:
            variables.extend(self.extract_postman_variables(parsed_curl.body))

        # check query parameters
        if parsed_curl.query_params:
            for param_name, param_value in parsed_curl.query_params.items():
                variables.extend(self.extract_postman_variables(param_name))
                variables.extend(self.extract_postman_variables(param_value))

        return list(set(variables))  # Remove duplicates

    def to_postman_request(
        self, parsed_curl: ParsedCurl, name: str, description: str = ""
    ) -> dict[str, Any]:
        """Convert parsed cURL to Postman request format."""
        # build headers array
        headers_array = []
        for header_name, header_value in parsed_curl.headers.items():
            headers_array.append(
                {"key": header_name, "value": header_value, "type": "text"}
            )

        # build query parameters array
        query_array = []
        if parsed_curl.query_params:
            for param_name, param_value in parsed_curl.query_params.items():
                query_array.append({"key": param_name, "value": param_value})

        # build request body
        body = None
        if parsed_curl.body:
            try:
                json_data = json.loads(parsed_curl.body)
                body = {
                    "mode": "raw",
                    "raw": json.dumps(json_data, indent=2),
                    "options": {"raw": {"language": "json"}},
                }
            except (json.JSONDecodeError, TypeError):
                # if not valid JSON, treat as raw text
                body = {"mode": "raw", "raw": parsed_curl.body}

        request = {
            "name": name,
            "request": {
                "method": parsed_curl.method,
                "header": headers_array,
                "url": {
                    "raw": parsed_curl.url
                    + (
                        "?"
                        + "&".join(
                            f"{k}={v}" for k, v in parsed_curl.query_params.items()
                        )
                        if parsed_curl.query_params
                        else ""
                    ),
                    "protocol": urlparse(parsed_curl.url).scheme or "https",
                    "host": (urlparse(parsed_curl.url).netloc or "").split("."),
                    "path": (urlparse(parsed_curl.url).path or "/")
                    .strip("/")
                    .split("/")
                    if urlparse(parsed_curl.url).path
                    and urlparse(parsed_curl.url).path != "/"
                    else [],
                    "query": query_array,
                },
            },
        }

        if body:
            request["request"]["body"] = body

        if description:
            request["request"]["description"] = description

        return request
