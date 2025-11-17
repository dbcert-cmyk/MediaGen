"""
MCP Server: Database Operations

Exposes SQLite database tools for the agent to query and manipulate data.
"""

import sqlite3
import json
from typing import Any, Sequence
from mcp.server import Server
from mcp.types import Tool, TextContent
import os

# Server instance
server = Server("database-server")

# Database path
DB_PATH = os.getenv("DATABASE_PATH", "data/demo.db")


def get_db_connection():
    """Get a database connection"""
    return sqlite3.connect(DB_PATH)


def dict_factory(cursor, row):
    """Convert database row to dictionary"""
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available database tools"""
    return [
        Tool(
            name="query_database",
            description="Execute a SELECT query on the SQLite database. Returns results as JSON.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL SELECT query to execute"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_table_schema",
            description="Get the schema (structure) of a database table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table"
                    }
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="list_tables",
            description="List all tables in the database",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_statistics",
            description="Get statistics about the database (row counts, etc.)",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="insert_record",
            description="Insert a new record into a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table"
                    },
                    "data": {
                        "type": "object",
                        "description": "Key-value pairs of column names and values"
                    }
                },
                "required": ["table_name", "data"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Handle tool calls"""

    if name == "query_database":
        return await query_database(arguments.get("query"))

    elif name == "get_table_schema":
        return await get_table_schema(arguments.get("table_name"))

    elif name == "list_tables":
        return await list_tables()

    elif name == "get_statistics":
        return await get_statistics()

    elif name == "insert_record":
        return await insert_record(
            arguments.get("table_name"),
            arguments.get("data")
        )

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def query_database(query: str) -> Sequence[TextContent]:
    """Execute a SELECT query"""
    try:
        # Security: Only allow SELECT statements
        if not query.strip().upper().startswith("SELECT"):
            return [TextContent(
                type="text",
                text="Error: Only SELECT queries are allowed for security"
            )]

        conn = get_db_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        cursor.execute(query)
        results = cursor.fetchall()

        conn.close()

        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "row_count": len(results),
                "data": results
            }, indent=2)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            })
        )]


async def get_table_schema(table_name: str) -> Sequence[TextContent]:
    """Get table schema"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        conn.close()

        schema = []
        for col in columns:
            schema.append({
                "name": col[1],
                "type": col[2],
                "nullable": not col[3],
                "primary_key": bool(col[5])
            })

        return [TextContent(
            type="text",
            text=json.dumps({
                "table": table_name,
                "columns": schema
            }, indent=2)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e)
            })
        )]


async def list_tables() -> Sequence[TextContent]:
    """List all tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)

        tables = [row[0] for row in cursor.fetchall()]

        conn.close()

        return [TextContent(
            type="text",
            text=json.dumps({
                "tables": tables,
                "count": len(tables)
            }, indent=2)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e)
            })
        )]


async def get_statistics() -> Sequence[TextContent]:
    """Get database statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        tables = [row[0] for row in cursor.fetchall()]

        # Get row counts
        stats = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            stats[table] = count

        conn.close()

        return [TextContent(
            type="text",
            text=json.dumps({
                "database": DB_PATH,
                "table_count": len(tables),
                "row_counts": stats,
                "total_rows": sum(stats.values())
            }, indent=2)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e)
            })
        )]


async def insert_record(table_name: str, data: dict) -> Sequence[TextContent]:
    """Insert a record into a table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        values = tuple(data.values())

        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)

        conn.commit()
        new_id = cursor.lastrowid
        conn.close()

        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "table": table_name,
                "inserted_id": new_id
            }, indent=2)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
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
