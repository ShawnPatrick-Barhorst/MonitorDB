from monitordb.integrations.base import Integration
from monitordb.integrations.google_health_connect.mcp import health_connect_mcp
from monitordb.integrations.google_health_connect.route import health_connect_router
from monitordb.integrations.google_health_connect.schema import (
    init_health_connect_tables,
)

INTEGRATION = Integration(
    name="google_health_connect",
    build_schema=init_health_connect_tables,
    router=health_connect_router,
    mcp=health_connect_mcp,
)
