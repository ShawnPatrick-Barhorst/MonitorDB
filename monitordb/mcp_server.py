from fastmcp import FastMCP

from monitordb.integrations import discover

mcp = FastMCP(
    name="MonitorDB Tools",
    instructions="Monitoring tools to query health metrics, calendar events, sleep sessions, etc, from MonitorDB.",
)

for integration in discover():
    if integration.mcp is not None:
        mcp.mount(integration.mcp)


@mcp.tool
def ping() -> dict[str, str]:
    """Probe to check if the monitorDB MCP server is running"""
    return {"status": "alive"}
