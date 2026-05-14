import os
import json
import asyncio
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="GIS Data Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

current: dict = {}
connected_clients: set[WebSocket] = set()


class SetBody(BaseModel):
    type: str
    data: list
    isFinal: bool = False


class FinalBody(BaseModel):
    isFinal: bool


async def broadcast():
    if not connected_clients:
        return
    msg = json.dumps(current, ensure_ascii=False)
    await asyncio.gather(
        *(client.send_text(msg) for client in connected_clients),
        return_exceptions=True,
    )


@app.post("/api/set")
async def set_data(body: SetBody):
    current.clear()
    current["isFinal"] = body.isFinal
    current["type"] = body.type
    current["data"] = body.data
    await broadcast()
    return {"ok": True}


@app.patch("/api/final")
async def set_final(body: FinalBody):
    if not current:
        raise HTTPException(400, "no data set yet")
    current["isFinal"] = body.isFinal
    await broadcast()
    return {"ok": True}


@app.get("/api/data")
def get_data():
    return current


@app.websocket("/ws/data")
async def ws_data(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        await websocket.send_text(json.dumps(current, ensure_ascii=False))
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connected_clients.discard(websocket)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("DATA_SERVER_PORT", "8000"))
    uvicorn.run("server.app:app", host="0.0.0.0", port=port, reload=True)
