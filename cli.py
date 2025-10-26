"""
CLI tool for converting Markdown to Postman Collections.
"""

import argparse
import os
import sys
from pathlib import Path

from md_to_postman.markdown_parser import MarkdownParser
from md_to_postman.postman_builder import PostmanCollectionBuilder


def main():
    parser = argparse.ArgumentParser(
        description="Convert structured Markdown files to Postman Collections v2.1"
    )

    parser.add_argument("input_file", help="Path to the markdown file to convert")

    parser.add_argument(
        "-o",
        "--output",
        help="Output file path (default: <input_file>.postman_collection.json)",
    )

    parser.add_argument(
        "-n", "--name", help="Collection name (default: input filename)"
    )

    parser.add_argument(
        "-d",
        "--description",
        default="Collection generated from Markdown",
        help="Collection description",
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Only validate the markdown structure without conversion",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: File '{args.input_file}' not found", file=sys.stderr)
        return 1

    try:
        # Read input file
        with open(args.input_file, encoding="utf-8") as file:
            markdown_content = file.read()

        # Parse markdown
        parser_obj = MarkdownParser()
        requests = parser_obj.parse(markdown_content)

        if args.verbose:
            print(f"Parsed {len(requests)} requests from {args.input_file}")
            for req in requests:
                print(f"  - {req.name} (folder: {req.folder or 'root'})")

        if not requests:
            print(
                "Warning: No valid requests found in the markdown file", file=sys.stderr
            )
            if not args.validate:
                return 1

        # Validation mode
        if args.validate:
            print("✅ Markdown structure validation:")
            print(f"  Requests found: {len(requests)}")

            folders = set(req.folder for req in requests if req.folder)
            print(f"  Folders: {len(folders)}")
            if folders:
                for folder in sorted(folders):
                    print(f"    - {folder}")

            # Check for issues
            issues = []
            for req in requests:
                if not req.curl_command.strip():
                    issues.append(f"Request '{req.name}': Empty cURL command")
                if not req.metadata.description:
                    issues.append(f"Request '{req.name}': Missing description")

            if issues:
                print("  Issues found:")
                for issue in issues:
                    print(f"    ⚠️  {issue}")
            else:
                print("  ✅ No issues found")

            return 0

        # Generate collection name
        collection_name = args.name or Path(args.input_file).stem

        # Build collection
        builder = PostmanCollectionBuilder()
        collection = builder.build_collection(
            requests, collection_name, args.description
        )

        # Generate output filename
        output_file = args.output
        if not output_file:
            input_path = Path(args.input_file)
            output_file = str(
                input_path.parent / f"{input_path.stem}.postman_collection.json"
            )

        # Save collection
        builder.save_collection(collection, output_file)

        print("✅ Postman collection generated successfully!")
        print(f"   Input: {args.input_file}")
        print(f"   Output: {output_file}")
        print(f"   Requests: {len(requests)}")
        print(f"   Folders: {len(set(req.folder for req in requests if req.folder))}")
        print(f"   Variables: {len(collection.get('variable', []))}")

        return 0

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
