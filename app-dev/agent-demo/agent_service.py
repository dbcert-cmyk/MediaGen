"""
Google Agent Kit Integration

This module integrates Google's Gemini model with MCP servers
to create an intelligent agent that can orchestrate data movement
across multiple data sources.
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Callable
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Import MCP servers
from mcp_servers import database_server, filesystem_server, api_server

# Load environment variables
load_dotenv()


class AgentService:
    """
    Google Agent Kit service that orchestrates MCP servers
    """

    def __init__(self):
        """Initialize the agent service"""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")

        # Initialize Google GenAI client
        self.client = genai.Client(api_key=self.api_key)

        # Model to use (Gemini 2.5 Flash with function calling)
        self.model_id = "gemini-2.5-flash"

        # Available tools from MCP servers
        self.function_declarations = []
        self.tool_handlers = {}

        # Activity log for tracking
        self.activity_log = []

        # Initialize tools
        asyncio.run(self._initialize_tools())

    async def _initialize_tools(self):
        """Initialize tools from all MCP servers"""
        self.log_activity("system", "Initializing MCP servers...")

        # Get tools from each server
        db_tools = await database_server.list_tools()
        fs_tools = await filesystem_server.list_tools()
        api_tools = await api_server.list_tools()

        # Convert MCP tools to Google function declarations
        for tool in db_tools:
            self._register_tool(tool, database_server, "database")

        for tool in fs_tools:
            self._register_tool(tool, filesystem_server, "filesystem")

        for tool in api_tools:
            self._register_tool(tool, api_server, "api")

        self.log_activity("system", f"Initialized {len(self.function_declarations)} tools from 3 MCP servers")

    def _register_tool(self, mcp_tool, server, server_type):
        """Register an MCP tool for use with the agent"""
        # Convert MCP tool schema to Google function declaration
        function_declaration = types.FunctionDeclaration(
            name=mcp_tool.name,
            description=mcp_tool.description,
            parameters=mcp_tool.inputSchema
        )

        self.function_declarations.append(function_declaration)

        # Store handler
        self.tool_handlers[mcp_tool.name] = {
            "server": server,
            "server_type": server_type,
            "handler": server.call_tool
        }

    def log_activity(self, activity_type: str, message: str, data: Any = None):
        """Log activity for tracking"""
        activity = {
            "type": activity_type,
            "message": message,
            "data": data,
            "timestamp": asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
        }
        self.activity_log.append(activity)
        print(f"[{activity_type.upper()}] {message}")

    async def execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """Execute a tool call via MCP server"""
        if tool_name not in self.tool_handlers:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        handler_info = self.tool_handlers[tool_name]
        server_type = handler_info["server_type"]

        self.log_activity(
            "tool_call",
            f"Calling {tool_name} on {server_type} MCP server",
            {"arguments": arguments}
        )

        try:
            # Create arguments object
            class Args:
                def __init__(self, **kwargs):
                    for key, value in kwargs.items():
                        setattr(self, key, value)

                def get(self, key, default=None):
                    return getattr(self, key, default)

            args = Args(**arguments)

            # Call the MCP server tool
            result = await handler_info["handler"](tool_name, args)

            # Extract text from result
            if result and len(result) > 0:
                response_text = result[0].text
                self.log_activity(
                    "tool_response",
                    f"Received response from {tool_name}",
                    {"response_length": len(response_text)}
                )
                return response_text
            else:
                return json.dumps({"error": "No response from tool"})

        except Exception as e:
            error_msg = f"Error executing {tool_name}: {str(e)}"
            self.log_activity("error", error_msg)
            return json.dumps({"error": error_msg})

    async def query(self, user_query: str, on_progress: Callable = None) -> Dict[str, Any]:
        """
        Process a user query using the agent

        Args:
            user_query: The user's natural language query
            on_progress: Optional callback for progress updates

        Returns:
            Dict with response and activity log
        """
        self.log_activity("user_query", user_query)

        if on_progress:
            on_progress({"type": "started", "message": "Agent processing query..."})

        try:
            # Create tool with all function declarations
            tool = types.Tool(
                function_declarations=self.function_declarations
            )

            # Create the chat with tools
            chat = self.client.chats.create(
                model=self.model_id,
                config=types.GenerateContentConfig(
                    tools=[tool],
                    temperature=0.1,  # Low temperature for more deterministic responses
                )
            )

            # Send the user query
            response = chat.send_message(user_query)

            # Process function calls
            turn_count = 0
            max_turns = 10  # Prevent infinite loops

            while turn_count < max_turns:
                turn_count += 1

                # Check if there are function calls
                if not response.candidates or not response.candidates[0].content.parts:
                    break

                parts = response.candidates[0].content.parts
                function_calls = [part for part in parts if hasattr(part, 'function_call')]

                if not function_calls:
                    # No more function calls, we have the final response
                    break

                # Execute all function calls
                function_responses = []
                for fc_part in function_calls:
                    fc = fc_part.function_call

                    # Safety check
                    if not fc or not hasattr(fc, 'name'):
                        continue

                    if on_progress:
                        on_progress({
                            "type": "tool_call",
                            "tool": fc.name,
                            "server": self.tool_handlers.get(fc.name, {}).get("server_type", "unknown")
                        })

                    # Execute the function
                    args_dict = dict(fc.args) if hasattr(fc, 'args') and fc.args else {}
                    result = await self.execute_tool(fc.name, args_dict)

                    # Create function response
                    function_responses.append(
                        types.Part.from_function_response(
                            name=fc.name,
                            response={"result": result}
                        )
                    )

                # Send function responses back to the model
                response = chat.send_message(function_responses)

            # Extract final response
            if response.candidates and response.candidates[0].content.parts:
                final_text = ""
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text'):
                        final_text += part.text

                self.log_activity("agent_response", "Query completed successfully")

                if on_progress:
                    on_progress({"type": "completed", "message": "Query completed"})

                return {
                    "success": True,
                    "response": final_text,
                    "activity_log": self.activity_log.copy(),
                    "turns": turn_count
                }
            else:
                return {
                    "success": False,
                    "error": "No response from agent",
                    "activity_log": self.activity_log.copy()
                }

        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            self.log_activity("error", error_msg)

            if on_progress:
                on_progress({"type": "error", "message": error_msg})

            return {
                "success": False,
                "error": error_msg,
                "activity_log": self.activity_log.copy()
            }

    def clear_activity_log(self):
        """Clear the activity log"""
        self.activity_log = []

    def get_available_tools(self) -> List[Dict]:
        """Get list of available tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "server": self.tool_handlers[tool.name]["server_type"]
            }
            for tool in self.function_declarations
        ]


# Singleton instance
_agent_service = None


def get_agent_service() -> AgentService:
    """Get or create the agent service singleton"""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service


# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize agent
        agent = get_agent_service()

        # List available tools
        print("\nAvailable tools:")
        for tool in agent.get_available_tools():
            print(f"  - {tool['name']} ({tool['server']}): {tool['description']}")

        # Example query
        print("\n" + "="*60)
        print("Testing agent with sample query...")
        print("="*60)

        result = await agent.query("How many orders are in the database?")

        if result["success"]:
            print(f"\nAgent Response: {result['response']}")
            print(f"Function calls made: {result['turns']}")
        else:
            print(f"\nError: {result['error']}")

        print("\nActivity Log:")
        for activity in result['activity_log']:
            print(f"  [{activity['type']}] {activity['message']}")

    asyncio.run(main())
