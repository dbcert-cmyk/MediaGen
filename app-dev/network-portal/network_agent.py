"""
Network Management Agent
Uses Google Gemini + MCP servers for intelligent network management
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Callable
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Import MCP server
from mcp_servers import network_query_server

# Load environment
load_dotenv()


class NetworkAgent:
    """
    Intelligent network management agent powered by Google Gemini
    """

    def __init__(self, server_monitor, wifi_monitor, switch_monitor):
        """
        Initialize the network agent

        Args:
            server_monitor: ServerMonitor instance
            wifi_monitor: WiFiMonitor instance
            switch_monitor: SwitchMonitor instance
        """
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment. Please add it to .env file")

        # Initialize Google GenAI client
        self.client = genai.Client(api_key=self.api_key)

        # Model to use
        self.model_id = "gemini-2.5-flash-latest"

        # Inject monitors into MCP server
        network_query_server.set_monitors(server_monitor, wifi_monitor, switch_monitor)

        # Available tools
        self.function_declarations = []
        self.tool_handlers = {}

        # Activity log
        self.activity_log = []

        # Initialize tools
        asyncio.run(self._initialize_tools())

    async def _initialize_tools(self):
        """Initialize tools from MCP servers"""
        self.log_activity("system", "Initializing Network Agent with MCP servers...")

        # Get tools from network query server
        tools = await network_query_server.list_tools()

        # Register each tool
        for tool in tools:
            self._register_tool(tool, network_query_server, "network")

        self.log_activity("system", f"Initialized {len(self.function_declarations)} network management tools")

    def _register_tool(self, mcp_tool, server, server_type):
        """Register an MCP tool for use with the agent"""
        # Convert MCP tool to Google function declaration
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
        """Log activity"""
        activity = {
            "type": activity_type,
            "message": message,
            "data": data
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
            f"Calling {tool_name} on {server_type} server",
            {"arguments": arguments}
        )

        try:
            # Call the MCP server tool
            result = await handler_info["handler"](tool_name, arguments)

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
        Process a user query about the network

        Args:
            user_query: Natural language query from user
            on_progress: Optional callback for progress updates

        Returns:
            Dict with response and activity log
        """
        self.log_activity("user_query", user_query)

        # Track workflow steps
        workflow_steps = []
        current_step = 0

        if on_progress:
            on_progress({"type": "started", "message": "Agent analyzing network..."})

        try:
            # Create tool with all function declarations
            tool = types.Tool(
                function_declarations=self.function_declarations
            )

            # Create system instruction for network context
            system_instruction = """You are an intelligent network management assistant.

Your role is to help users understand and manage their home/office network including:
- Servers (Linux/Windows machines, NAS, etc.)
- WiFi Access Points
- Network switches

When answering questions:
1. Be concise and helpful
2. Explain technical issues in simple terms
3. Provide actionable recommendations
4. Always check current device status before answering
5. If devices are offline or having issues, explain possible causes
6. Format data clearly (use bullet points, numbers where helpful)

Available tools let you query real-time network stats. Always use tools to get current information before answering."""

            # Create the chat with tools and system instruction
            chat = self.client.chats.create(
                model=self.model_id,
                config=types.GenerateContentConfig(
                    tools=[tool],
                    temperature=0.2,  # Lower temperature for more factual responses
                    system_instruction=system_instruction
                )
            )

            # Send the user query
            response = chat.send_message(user_query)

            # Process function calls
            turn_count = 0
            max_turns = 10

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

                    # Track this step
                    current_step += 1
                    step_info = {
                        "step": current_step,
                        "tool": fc.name,
                        "server": self.tool_handlers.get(fc.name, {}).get("server_type", "unknown"),
                        "args": dict(fc.args) if hasattr(fc, 'args') and fc.args else {}
                    }
                    workflow_steps.append(step_info)

                    if on_progress:
                        on_progress({
                            "type": "tool_call",
                            "tool": fc.name,
                            "server": step_info["server"],
                            "step": current_step
                        })

                    # Execute the function
                    args_dict = dict(fc.args) if hasattr(fc, 'args') and fc.args else {}
                    result = await self.execute_tool(fc.name, args_dict)

                    # Update step with result
                    step_info["completed"] = True

                    # Create function response
                    function_responses.append(
                        types.Part.from_function_response(
                            name=fc.name,
                            response={"result": result}
                        )
                    )

                # Send function responses back to the model
                if function_responses:
                    response = chat.send_message(
                        types.Content(
                            role="user",
                            parts=function_responses
                        )
                    )

            # Extract final response
            if response.candidates and response.candidates[0].content.parts:
                final_text = ""
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text'):
                        final_text += part.text

                self.log_activity("agent_response", "Query completed successfully")

                if on_progress:
                    on_progress({
                        "type": "completed",
                        "message": "Analysis complete",
                        "workflow_steps": workflow_steps,
                        "total_steps": current_step
                    })

                return {
                    "success": True,
                    "response": final_text,
                    "activity_log": self.activity_log.copy(),
                    "turns": turn_count,
                    "workflow_steps": workflow_steps,
                    "total_steps": current_step
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
