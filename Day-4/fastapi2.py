from fastapi import FastAPI, WebSocket, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from jose import jwt
import time

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware
@app.middleware("http")
async def log(request, call_next):
    print("request")
    return await call_next(request)

# JWT
SECRET = "secret"

def check(token: str):
    try:
        return jwt.decode(token, SECRET, ["HS256"])["user"]
    except:
        raise HTTPException(401, "bad token")

# Background task
def bg():
    time.sleep(2)
    print("background done")

@app.post("/task")
def task(bg_tasks: BackgroundTasks):
    bg_tasks.add_task(bg)
    return {"msg": "started"}

# Streaming
@app.get("/stream")
def stream():
    def gen():
        for i in range(5):
            yield f"{i}\n"
            time.sleep(1)
    return StreamingResponse(gen())

# Protected
@app.get("/secure")
def secure(token: str):
    return {"user": check(token)}

# WebSocket
@app.websocket("/ws")
async def ws(ws: WebSocket):
    await ws.accept()
    while True:
        msg = await ws.receive_text()
        await ws.send_text(msg)