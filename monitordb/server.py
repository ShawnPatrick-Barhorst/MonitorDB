import logging

from monitordb.integrations import discover

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

from fastapi import FastAPI

app = FastAPI(title="MonitorDB")

for integration in discover():
    if integration.router is not None:
        app.include_router(integration.router)


@app.get("/biometric")
async def health_check():
    return {"status": "alive"}
