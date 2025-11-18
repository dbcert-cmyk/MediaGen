"""
AI Agent Manager using Ollama and LangChain
"""
import os
import logging
from typing import Optional, Dict
from langchain_community.llms import Ollama
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain import hub
from langchain.memory import ConversationBufferMemory

from mcp_servers.network_scanner import scan_network
from mcp_servers.ssh_manager import execute_ssh_command
from mcp_servers.device_info import get_device_info

logger = logging.getLogger(__name__)

class AgentManager:
    """Manages the AI agent for network operations"""

    def __init__(self):
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
        self.model_name = os.getenv("OLLAMA_MODEL", "llama3.2")
        self.llm: Optional[Ollama] = None
        self.agent: Optional[AgentExecutor] = None
        self.memory = ConversationBufferMemory(memory_key="chat_history")
        self._ready = False

    async def initialize(self):
        """Initialize the AI agent and tools"""
        try:
            logger.info(f"Initializing Ollama connection to {self.ollama_host}")

            # Initialize Ollama LLM
            self.llm = Ollama(
                base_url=self.ollama_host,
                model=self.model_name,
                temperature=0.7
            )

            # Test connection
            try:
                response = self.llm.invoke("Hello")
                logger.info("Ollama connection successful")
            except Exception as e:
                logger.warning(f"Ollama not ready, will retry: {e}")
                # Mark as not ready but don't fail - it might start later
                return

            # Define tools for the agent
            tools = [
                Tool(
                    name="NetworkScan",
                    func=lambda subnet: self._run_async(scan_network(subnet, "discovery")),
                    description="Scan a network subnet to discover devices. Input should be a subnet in CIDR notation (e.g., '192.168.1.0/24')"
                ),
                Tool(
                    name="DeviceInfo",
                    func=lambda device_id: self._run_async(get_device_info(int(device_id))),
                    description="Get detailed information about a specific device. Input should be a device ID number."
                ),
                Tool(
                    name="ExecuteSSH",
                    func=lambda params: self._run_async(self._execute_ssh_wrapper(params)),
                    description="Execute a command on a remote device via SSH. Input should be a JSON string with 'host', 'username', 'command' keys."
                )
            ]

            # Create agent
            # Using a simple system prompt for now
            prompt_template = """You are a helpful network management assistant. You have access to tools to scan networks, get device information, and execute commands via SSH.

You should help users manage their home network by:
1. Discovering and monitoring devices
2. Checking device status and health
3. Executing network operations
4. Troubleshooting connectivity issues
5. Providing network insights and recommendations

Available tools:
{tools}

Tool names: {tool_names}

When asked to perform a task:
1. Think about which tools you need to use
2. Use the tools to gather information
3. Provide a clear, helpful response

Question: {input}
{agent_scratchpad}
"""

            # For now, use a simple approach without hub.pull
            from langchain.agents import initialize_agent, AgentType

            self.agent = initialize_agent(
                tools=tools,
                llm=self.llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                memory=self.memory,
                handle_parsing_errors=True
            )

            self._ready = True
            logger.info("AI Agent initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize AI agent: {e}")
            self._ready = False

    async def process_query(self, query: str, context: Optional[Dict] = None) -> str:
        """Process a user query with the AI agent"""
        if not self._ready or not self.agent:
            return "AI agent is not ready. Please ensure Ollama is running and the model is downloaded."

        try:
            # Add context to query if provided
            full_query = query
            if context:
                full_query = f"Context: {context}\n\nQuery: {query}"

            # Run agent
            response = self.agent.invoke({"input": full_query})

            return response.get("output", "No response generated")

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"Error: {str(e)}"

    def is_ready(self) -> bool:
        """Check if agent is ready"""
        return self._ready

    def get_model_info(self) -> Dict:
        """Get information about the current model"""
        return {
            "model": self.model_name,
            "host": self.ollama_host,
            "ready": self._ready
        }

    async def shutdown(self):
        """Cleanup resources"""
        logger.info("Shutting down AI agent")
        self._ready = False

    def _run_async(self, coro):
        """Helper to run async functions in sync context"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

    async def _execute_ssh_wrapper(self, params: str):
        """Wrapper for SSH execution"""
        import json
        try:
            p = json.loads(params)
            return await execute_ssh_command(
                host=p["host"],
                username=p["username"],
                command=p["command"],
                password=p.get("password")
            )
        except Exception as e:
            return {"error": str(e)}
