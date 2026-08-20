from fastapi import APIRouter, HTTPException, Request
from pydantic import ValidationError

from monitordb.integrations.google_health_connect.sync import health_connect_sync

health_connect_router = APIRouter(prefix="/health-connect")


@health_connect_router.post("/webhook")
async def webhook(request: Request):
    payload = await request.json()
    try:
        result = health_connect_sync(payload)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    return {"status": "ok", **result}
