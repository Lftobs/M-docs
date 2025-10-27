"""
Markdown parser for extracting cURL requests and metadata.
"""

import re
from dataclasses import dataclass


@dataclass
class RequestMetadata:
    """Metadata extracted from markdown for a single request."""

    description: str | None = None
    requires: str | None = None
    save_response_variable: str | None = None


@dataclass
class ParsedRequest:
    """A parsed request containing metadata and cURL command."""

    name: str
    metadata: RequestMetadata
    curl_command: str
    folder: str | None = None


class MarkdownParser:
    """Parser for structured markdown files containing cURL requests."""

    def __init__(self):
        self.metadata_pattern = re.compile(
            r"^\*\*([^:]+):\*\*\s*(.*)$"
        )  # matches key and value; value can be empty
        self.curl_block_pattern = re.compile(r"```curl\n(.*?)\n```", re.DOTALL)

    def parse(self, markdown_content: str) -> list[ParsedRequest]:
        """Parse markdown content and extract structured requests."""
        lines = markdown_content.split("\n")
        requests = []
        current_folder = None
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            if line.startswith("# ") and not line.startswith("## "):
                current_folder = line[2:].strip()
                i += 1
                continue

            # Check for request name H2 ( which is mapped as the request item
            # with a folder (which is mapped as H1)
            if line.startswith("## "):
                request_name = line[3:].strip()
                metadata, curl_command, next_i = self._parse_request_block(lines, i + 1)

                if curl_command:
                    parsed_request = ParsedRequest(
                        name=request_name,
                        metadata=metadata,
                        curl_command=curl_command,
                        folder=current_folder,
                    )
                    requests.append(parsed_request)

                i = next_i
                continue

            i += 1

        return requests

    def _parse_request_block(
        self, lines: list[str], start_index: int
    ) -> tuple[RequestMetadata, str | None, int]:
        """Parse a single request block starting from the given index."""
        metadata = RequestMetadata()
        curl_command = None
        i = start_index

        while i < len(lines):
            line = lines[i].strip()

            if line.startswith("#") or (
                not line
                and i + 1 < len(lines)
                and lines[i + 1].strip().startswith("```")
            ):
                break

            if line:
                match = self.metadata_pattern.match(line)
                if match:
                    field_name = match.group(1).strip().lower().replace(" ", "_")
                    field_value = match.group(2).strip()

                    if field_name == "description":
                        metadata.description = field_value
                    elif field_name == "requires":
                        metadata.requires = field_value
                    elif field_name == "save_response_variable":
                        metadata.save_response_variable = field_value

            i += 1

        # check for cURL block
        remaining_content = "\n".join(lines[i:])
        curl_match = self.curl_block_pattern.search(remaining_content)

        if curl_match:
            curl_command = curl_match.group(1).strip()
            curl_block_lines = curl_match.group(0).count("\n")

            curl_start_newlines = remaining_content[: curl_match.start()].count("\n")
            i += curl_block_lines + curl_start_newlines

        return metadata, curl_command, i

    def parse_file(self, file_path: str) -> list[ParsedRequest]:
        """Parse a markdown file and return parsed requests."""
        with open(file_path, encoding="utf-8") as file:
            content = file.read()
        return self.parse(content)
