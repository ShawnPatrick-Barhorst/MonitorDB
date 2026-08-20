from fastmcp import FastMCP

from monitordb.integrations.google_health_connect.mcp import health_connect_mcp

mcp = FastMCP(
    name="MonitorDB Tools",
    instructions="Monitoring tools to query health metrics, calendar events, sleep sessions, etc, from MonitorDB.",
)

mcp.mount(health_connect_mcp)


@mcp.tool
def ping() -> dict[str, str]:
    """Probe to check if the monitorDB MCP server is running"""
    return {"status": "alive"}
