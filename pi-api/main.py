from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import psutil
import socket
from collections import deque

app = FastAPI()

# Allow CORS so UI apps on other origins can request
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store last 60 stats submissions
stats_storage = deque(maxlen=60)

@app.post("/stats")
async def post_stats(request: Request):
    data = await request.json()
    if not data:
        raise HTTPException(status_code=400, detail="No JSON body received")

    stats_storage.append(data)
    return {"message": "Stats received", "stored": len(stats_storage)}

@app.get("/stats")
def get_stats():
    return list(stats_storage)

@app.get("/ips")
def get_ips():
    ips = []
    for iface_addrs in psutil.net_if_addrs().values():
        for addr in iface_addrs:
            if addr.family == socket.AF_INET:
                ips.append(addr.address)
    return {"ips": ips}
