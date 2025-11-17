"""
MCP Server: Mock API Operations

Simulates external API calls for demonstration purposes.
Provides mock data for weather, stocks, and sensor readings.
"""

import json
import random
from datetime import datetime
from typing import Any, Sequence
from mcp.server import Server
from mcp.types import Tool, TextContent

# Server instance
server = Server("api-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available API tools"""
    return [
        Tool(
            name="get_weather",
            description="Get current weather for a city (mock data)",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name"
                    }
                },
                "required": ["city"]
            }
        ),
        Tool(
            name="get_stock_price",
            description="Get stock price for a symbol (mock data)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., GOOGL, AAPL)"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_sensor_reading",
            description="Get latest IoT sensor reading (mock data)",
            inputSchema={
                "type": "object",
                "properties": {
                    "sensor_id": {
                        "type": "string",
                        "description": "Sensor ID"
                    }
                },
                "required": ["sensor_id"]
            }
        ),
        Tool(
            name="search_products",
            description="Search for products in catalog (mock data)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_exchange_rate",
            description="Get currency exchange rate (mock data)",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_currency": {
                        "type": "string",
                        "description": "Source currency code (e.g., USD)"
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "Target currency code (e.g., EUR)"
                    }
                },
                "required": ["from_currency", "to_currency"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Handle tool calls"""

    if name == "get_weather":
        return await get_weather(arguments.get("city"))

    elif name == "get_stock_price":
        return await get_stock_price(arguments.get("symbol"))

    elif name == "get_sensor_reading":
        return await get_sensor_reading(arguments.get("sensor_id"))

    elif name == "search_products":
        return await search_products(arguments.get("query"))

    elif name == "get_exchange_rate":
        return await get_exchange_rate(
            arguments.get("from_currency"),
            arguments.get("to_currency")
        )

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def get_weather(city: str) -> Sequence[TextContent]:
    """Get mock weather data"""
    # Mock weather conditions
    conditions = ["Sunny", "Cloudy", "Rainy", "Partly Cloudy", "Clear"]

    weather_data = {
        "city": city,
        "timestamp": datetime.now().isoformat(),
        "temperature": round(random.uniform(50, 85), 1),
        "humidity": random.randint(30, 80),
        "condition": random.choice(conditions),
        "wind_speed": round(random.uniform(5, 25), 1),
        "pressure": round(random.uniform(29.5, 30.5), 2),
        "source": "mock_api"
    }

    return [TextContent(
        type="text",
        text=json.dumps(weather_data, indent=2)
    )]


async def get_stock_price(symbol: str) -> Sequence[TextContent]:
    """Get mock stock price"""

    # Base prices for common stocks
    base_prices = {
        "GOOGL": 142.50,
        "AAPL": 195.30,
        "MSFT": 378.90,
        "AMZN": 175.20,
        "TSLA": 242.80,
        "META": 485.60,
        "NVDA": 875.40
    }

    base_price = base_prices.get(symbol.upper(), random.uniform(50, 500))

    # Add random variation
    variation = random.uniform(-5, 5)
    current_price = round(base_price + variation, 2)
    change = round(variation, 2)
    change_percent = round((variation / base_price) * 100, 2)

    stock_data = {
        "symbol": symbol.upper(),
        "timestamp": datetime.now().isoformat(),
        "price": current_price,
        "change": change,
        "change_percent": change_percent,
        "volume": random.randint(1000000, 50000000),
        "market_cap": f"${random.randint(500, 3000)}B",
        "source": "mock_api"
    }

    return [TextContent(
        type="text",
        text=json.dumps(stock_data, indent=2)
    )]


async def get_sensor_reading(sensor_id: str) -> Sequence[TextContent]:
    """Get mock sensor reading"""

    reading_data = {
        "sensor_id": sensor_id,
        "timestamp": datetime.now().isoformat(),
        "temperature": round(random.uniform(18, 28), 2),
        "humidity": round(random.uniform(35, 65), 2),
        "pressure": round(random.uniform(990, 1030), 2),
        "battery_level": random.randint(60, 100),
        "status": "online",
        "location": random.choice(["Warehouse A", "Office B", "Factory C"]),
        "source": "mock_api"
    }

    return [TextContent(
        type="text",
        text=json.dumps(reading_data, indent=2)
    )]


async def search_products(query: str) -> Sequence[TextContent]:
    """Search mock product catalog"""

    # Mock product database
    all_products = [
        {"id": 1, "name": "Laptop Pro 15", "category": "Electronics", "price": 1299.99, "stock": 45},
        {"id": 2, "name": "Wireless Mouse", "category": "Electronics", "price": 29.99, "stock": 150},
        {"id": 3, "name": "Mechanical Keyboard", "category": "Electronics", "price": 89.99, "stock": 80},
        {"id": 4, "name": "4K Monitor", "category": "Electronics", "price": 399.99, "stock": 30},
        {"id": 5, "name": "USB-C Hub", "category": "Electronics", "price": 49.99, "stock": 200},
        {"id": 6, "name": "Noise-Canceling Headphones", "category": "Electronics", "price": 249.99, "stock": 60},
        {"id": 7, "name": "Webcam HD", "category": "Electronics", "price": 79.99, "stock": 95},
        {"id": 8, "name": "Desk Lamp LED", "category": "Office", "price": 34.99, "stock": 120},
        {"id": 9, "name": "Ergonomic Chair", "category": "Office", "price": 299.99, "stock": 25},
        {"id": 10, "name": "Standing Desk", "category": "Office", "price": 499.99, "stock": 15},
    ]

    # Filter products based on query
    query_lower = query.lower()
    matching_products = [
        p for p in all_products
        if query_lower in p["name"].lower() or query_lower in p["category"].lower()
    ]

    result = {
        "query": query,
        "result_count": len(matching_products),
        "products": matching_products,
        "source": "mock_api"
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def get_exchange_rate(from_currency: str, to_currency: str) -> Sequence[TextContent]:
    """Get mock exchange rate"""

    # Mock base rates (relative to USD)
    rates = {
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "JPY": 149.50,
        "CAD": 1.36,
        "AUD": 1.53,
        "CHF": 0.88,
        "CNY": 7.24
    }

    from_rate = rates.get(from_currency.upper(), 1.0)
    to_rate = rates.get(to_currency.upper(), 1.0)

    # Calculate exchange rate
    exchange_rate = round(to_rate / from_rate, 4)

    # Add small random variation
    variation = random.uniform(-0.02, 0.02)
    exchange_rate += variation

    rate_data = {
        "from": from_currency.upper(),
        "to": to_currency.upper(),
        "rate": round(exchange_rate, 4),
        "timestamp": datetime.now().isoformat(),
        "inverse_rate": round(1 / exchange_rate, 4),
        "source": "mock_api"
    }

    return [TextContent(
        type="text",
        text=json.dumps(rate_data, indent=2)
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
