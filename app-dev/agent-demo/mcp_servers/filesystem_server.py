"""
MCP Server: Filesystem Operations

Exposes filesystem tools for searching and reading files.
"""

import os
import json
import glob
from typing import Any, Sequence
from mcp.server import Server
from mcp.types import Tool, TextContent

# Server instance
server = Server("filesystem-server")

# Data directory
DATA_DIR = os.getenv("DATA_DIR", "data/sample_files")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available filesystem tools"""
    return [
        Tool(
            name="list_files",
            description="List files in a directory with optional pattern matching",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory path (relative to data dir)",
                        "default": "."
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern (e.g., '*.json', '*.csv')",
                        "default": "*"
                    }
                }
            }
        ),
        Tool(
            name="read_file",
            description="Read contents of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file (relative to data dir)"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="search_files",
            description="Search for files by name or content pattern",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "Term to search for in filenames"
                    }
                },
                "required": ["search_term"]
            }
        ),
        Tool(
            name="get_file_info",
            description="Get metadata about a file (size, modified date, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="count_json_records",
            description="Count records/items in JSON files",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to JSON file"
                    }
                },
                "required": ["file_path"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Handle tool calls"""

    if name == "list_files":
        return await list_files(
            arguments.get("directory", "."),
            arguments.get("pattern", "*")
        )

    elif name == "read_file":
        return await read_file(arguments.get("file_path"))

    elif name == "search_files":
        return await search_files(arguments.get("search_term"))

    elif name == "get_file_info":
        return await get_file_info(arguments.get("file_path"))

    elif name == "count_json_records":
        return await count_json_records(arguments.get("file_path"))

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def list_files(directory: str = ".", pattern: str = "*") -> Sequence[TextContent]:
    """List files matching pattern"""
    try:
        if directory == ".":
            search_path = os.path.join(DATA_DIR, pattern)
        else:
            search_path = os.path.join(DATA_DIR, directory, pattern)

        files = glob.glob(search_path)

        # Get file info
        file_list = []
        for file_path in files:
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                file_list.append({
                    "name": os.path.basename(file_path),
                    "path": os.path.relpath(file_path, DATA_DIR),
                    "size_bytes": stat.st_size,
                    "modified": stat.st_mtime
                })

        return [TextContent(
            type="text",
            text=json.dumps({
                "directory": directory,
                "pattern": pattern,
                "file_count": len(file_list),
                "files": file_list
            }, indent=2)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e)
            })
        )]


async def read_file(file_path: str) -> Sequence[TextContent]:
    """Read file contents"""
    try:
        full_path = os.path.join(DATA_DIR, file_path)

        if not os.path.exists(full_path):
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"File not found: {file_path}"})
            )]

        # Check file size (limit to 1MB)
        if os.path.getsize(full_path) > 1024 * 1024:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "File too large (>1MB). Use get_file_info instead."
                })
            )]

        with open(full_path, 'r') as f:
            content = f.read()

        # Try to parse as JSON for better formatting
        try:
            data = json.loads(content)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "file": file_path,
                    "type": "json",
                    "content": data
                }, indent=2)
            )]
        except json.JSONDecodeError:
            # Return as plain text
            return [TextContent(
                type="text",
                text=json.dumps({
                    "file": file_path,
                    "type": "text",
                    "content": content[:1000]  # First 1000 chars
                }, indent=2)
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e)
            })
        )]


async def search_files(search_term: str) -> Sequence[TextContent]:
    """Search for files by name"""
    try:
        all_files = glob.glob(os.path.join(DATA_DIR, "**", "*"), recursive=True)

        matching_files = []
        for file_path in all_files:
            if os.path.isfile(file_path) and search_term.lower() in os.path.basename(file_path).lower():
                stat = os.stat(file_path)
                matching_files.append({
                    "name": os.path.basename(file_path),
                    "path": os.path.relpath(file_path, DATA_DIR),
                    "size_bytes": stat.st_size
                })

        return [TextContent(
            type="text",
            text=json.dumps({
                "search_term": search_term,
                "matches": len(matching_files),
                "files": matching_files
            }, indent=2)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e)
            })
        )]


async def get_file_info(file_path: str) -> Sequence[TextContent]:
    """Get file metadata"""
    try:
        full_path = os.path.join(DATA_DIR, file_path)

        if not os.path.exists(full_path):
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"File not found: {file_path}"})
            )]

        stat = os.stat(full_path)

        info = {
            "name": os.path.basename(file_path),
            "path": file_path,
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "modified": stat.st_mtime,
            "extension": os.path.splitext(file_path)[1]
        }

        return [TextContent(
            type="text",
            text=json.dumps(info, indent=2)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e)
            })
        )]


async def count_json_records(file_path: str) -> Sequence[TextContent]:
    """Count records in a JSON file"""
    try:
        full_path = os.path.join(DATA_DIR, file_path)

        if not os.path.exists(full_path):
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"File not found: {file_path}"})
            )]

        with open(full_path, 'r') as f:
            data = json.load(f)

        # Count based on structure
        if isinstance(data, list):
            count = len(data)
            record_type = "array_items"
        elif isinstance(data, dict):
            # Check for common patterns
            if "readings" in data and isinstance(data["readings"], list):
                count = len(data["readings"])
                record_type = "readings"
            else:
                count = len(data.keys())
                record_type = "object_keys"
        else:
            count = 1
            record_type = "single_value"

        return [TextContent(
            type="text",
            text=json.dumps({
                "file": file_path,
                "record_count": count,
                "record_type": record_type
            }, indent=2)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e)
            })
        )]


if __name__ == "__main__":
    # Run the server
    import asyncio
    from mcp.server.stdio import stdio_server

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )

    asyncio.run(main())
