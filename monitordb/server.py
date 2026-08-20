from fastapi import FastAPI

from monitordb.integrations.google_health_connect.route import health_connect_router

app = FastAPI(title="MonitorDB")

app.include_router(health_connect_router)


@app.get("/biometric")
async def health_check():
    return {"status": "alive"}
