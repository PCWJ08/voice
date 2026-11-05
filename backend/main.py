import os
import json
import asyncio
import random
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from voice_ai import audio_to_text
import game_ai 
import config

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR.parent / "static"

user_count = 0
last_activity_time = time.time() 
last_human_time = time.time()    

# 🌟 给永动机准备的话题池，防止复读
AUTO_TOPICS = [
    "（没人理我？你随机找个切入点狠狠的骂对方，不超过12字，别复读刚才的话了）",
    "（没人理我？你嘲讽一下对方刚才说的话，不超过12字，别讲和刚才一样的话了）",
    "（没人理我？你假装很懂地评价一下刚刚别人说的话，不超过12字，可以骂人哦）"
]

class ConnectionManager:
    def __init__(self):
        self.active_connections = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

async def reply_from_ai(ai_name: str, user_text: str, is_auto: bool = False):
    # 🌟 速度调快：0.4 到 1.0 秒，几乎是秒回
    await asyncio.sleep(random.uniform(0.4, 1.0))
    ai_reply_text = await game_ai.generate_ai_reply(ai_name, user_text)
    if not ai_reply_text:
        return
        
    print(f"[ AI ] {ai_name} 回复 -> \"{ai_reply_text}\"", flush=True)
    
    voice_id = config.AI_PERSONAS[ai_name]["voice"]
    ai_audio_base64 = await game_ai.text_to_base64_audio(ai_reply_text, voice_id, role=ai_name)
    
    if ai_audio_base64:
        ai_msgData = {
            "type": "voice",
            "sender": ai_name,
            "duration": max(1, len(ai_reply_text) // 4),
            "audio": f"data:audio/mp3;base64,{ai_audio_base64}"
        }
        await manager.broadcast(json.dumps(ai_msgData))

async def auto_chat_loop():
    global last_activity_time, last_human_time
    while True:
        await asyncio.sleep(5)
        now = time.time()
        
        if len(manager.active_connections) == 0:
            continue
            
        # 真人说话后，给 5 秒的缓冲期，防止打断
        if now - last_human_time < 5:
            continue

        if now - last_activity_time > 8:
            ai_list = list(config.AI_PERSONAS.keys())
            
            # 🌟 随机抽取一个话题，杜绝复读
            topic = random.choice(AUTO_TOPICS)
            
            if random.random() < 0.4:
                ai = random.choice(ai_list)
                asyncio.create_task(reply_from_ai(ai, topic, is_auto=True))
            else:
                for ai in ai_list:
                    asyncio.create_task(reply_from_ai(ai, topic, is_auto=True))
            last_activity_time = time.time()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(auto_chat_loop())

@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    global user_count, last_activity_time, last_human_time
    await manager.connect(websocket)
    user_count += 1
    # 如果名字带空格，我们也保留
    assigned_name = "圆周率" if user_count == 1 else f"圆周率_{user_count}"
    
    print(f"[连接] {assigned_name} 进入房间", flush=True)
    
    try:
        await websocket.send_text(f"SYSTEM_INIT::{assigned_name}")
    except Exception:
        pass

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msgData = json.loads(data)
                if msgData.get("type") == "voice":
                    sender = msgData.get("sender", "未知")
                    audio_base64 = msgData.get("audio", "")
                    
                    last_activity_time = time.time()
                    last_human_time = time.time()
                    
                    await manager.broadcast(data)
                    
                    user_text = await audio_to_text(audio_base64)
                    size_kb = len(audio_base64) / 1024
                    
                    print(f"\n[语音] {sender} 说({size_kb:.1f}KB) -> \"{user_text}\"", flush=True)

                    for ai_name in list(config.AI_PERSONAS.keys()):
                        asyncio.create_task(reply_from_ai(ai_name, user_text, is_auto=False))

            except Exception as e:
                print(f"❌ [处理报错]: {e}", flush=True)
            
    except WebSocketDisconnect:
        print(f"[断开] {assigned_name} 离开房间\n", flush=True)
        manager.disconnect(websocket)
        user_count -= 1
    except asyncio.CancelledError:
        print(f"[断开] {assigned_name} 异常断开", flush=True)
        manager.disconnect(websocket)
        user_count -= 1

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))