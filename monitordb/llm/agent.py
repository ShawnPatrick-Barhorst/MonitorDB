from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset

from monitordb.mcp_server import mcp

DEFAULT_PROMPT = "You are MonitorDB, a personal health and life-tracking assistant."


def build_agent(model: str, system_prompt: str = DEFAULT_PROMPT) -> Agent:
    return Agent(model, toolsets=[MCPToolset(mcp)], system_prompt=system_prompt)
