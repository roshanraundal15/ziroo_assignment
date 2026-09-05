"""
Ziroo assignment backend.

Core design choice:
  Per-user conversation context is stored separately.
  When @agent is called, ONLY that user's history is sent to the LLM.
  Shared room messages are still visible to everyone — isolation is about
  what the agent uses as context, not about hiding chat.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Dict, List, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from db import init_db, save_message, load_room_messages
from llm import call_llm

app = FastAPI(title="Ziroo Multiplayer Room")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

room_sockets: Dict[str, Set[WebSocket]] = {}
room_members: Dict[str, Dict[str, str]] = {}
user_context: Dict[str, Dict[str, List[Dict[str, str]]]] = {}
room_locks: Dict[str, asyncio.Lock] = {}


def get_lock(room_id: str) -> asyncio.Lock:
    if room_id not in room_locks:
        room_locks[room_id] = asyncio.Lock()
    return room_locks[room_id]


async def broadcast(room_id: str, payload: dict) -> None:
    dead: List[WebSocket] = []
    for ws in list(room_sockets.get(room_id, set())):
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        room_sockets.get(room_id, set()).discard(ws)


def members_payload(room_id: str) -> dict:
    members = [
        {"id": uid, "name": name}
        for uid, name in room_members.get(room_id, {}).items()
    ]
    return {"type": "members", "members": members}


def append_user_context(room_id: str, user_id: str, role: str, content: str) -> None:
    user_context.setdefault(room_id, {}).setdefault(user_id, []).append(
        {"role": role, "content": content}
    )
    if len(user_context[room_id][user_id]) > 30:
        user_context[room_id][user_id] = user_context[room_id][user_id][-30:]


@app.on_event("startup")
async def startup() -> None:
    await init_db()


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.get("/rooms/{room_id}/messages")
async def get_messages(room_id: str) -> dict:
    messages = await load_room_messages(room_id)
    return {"messages": messages}


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str) -> None:
    await websocket.accept()
    room_id = room_id.strip().lower()
    room_sockets.setdefault(room_id, set()).add(websocket)
    room_members.setdefault(room_id, {})

    user_id = str(uuid.uuid4())[:8]
    user_name = "Guest"

    history = await load_room_messages(room_id)
    await websocket.send_json(
        {
            "type": "welcome",
            "user_id": user_id,
            "room_id": room_id,
            "messages": history,
            "members": [
                {"id": uid, "name": name}
                for uid, name in room_members.get(room_id, {}).items()
            ],
        }
    )

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "join":
                user_name = (data.get("name") or "Guest").strip()[:32] or "Guest"
                room_members[room_id][user_id] = user_name
                await broadcast(
                    room_id,
                    {
                        "type": "system",
                        "content": f"{user_name} joined the room",
                        "created_at": time.time(),
                    },
                )
                await broadcast(room_id, members_payload(room_id))
                continue

            if msg_type == "chat":
                content = (data.get("content") or "").strip()
                if not content:
                    continue

                created_at = time.time()
                msg_id = await save_message(
                    room_id, user_id, user_name, "user", content, created_at
                )
                append_user_context(room_id, user_id, "user", content)

                await broadcast(
                    room_id,
                    {
                        "type": "chat",
                        "id": msg_id,
                        "room_id": room_id,
                        "user_id": user_id,
                        "user_name": user_name,
                        "role": "user",
                        "content": content,
                        "created_at": created_at,
                    },
                )

                lowered = content.lower().strip()
                if lowered.startswith("@agent"):
                    question = content[6:].strip() or content
                    asyncio.create_task(
                        handle_agent_reply(
                            room_id=room_id,
                            user_id=user_id,
                            user_name=user_name,
                            question=question,
                        )
                    )
                continue

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        room_sockets.get(room_id, set()).discard(websocket)
        left_name = room_members.get(room_id, {}).pop(user_id, user_name)
        await broadcast(
            room_id,
            {
                "type": "system",
                "content": f"{left_name} left the room",
                "created_at": time.time(),
            },
        )
        await broadcast(room_id, members_payload(room_id))
        if room_id in room_sockets and not room_sockets[room_id]:
            room_sockets.pop(room_id, None)


async def handle_agent_reply(
    room_id: str, user_id: str, user_name: str, question: str
) -> None:
    await broadcast(
        room_id,
        {
            "type": "agent_typing",
            "user_id": user_id,
            "user_name": user_name,
            "active": True,
        },
    )

    try:
        async with get_lock(room_id):
            history = list(user_context.get(room_id, {}).get(user_id, []))
            answer = await call_llm(user_name, history[:-1], question)
    except Exception as exc:
        answer = (
            f"Sorry {user_name}, something went wrong on my side "
            f"({type(exc).__name__}). Please try again."
        )

    created_at = time.time()
    msg_id = await save_message(
        room_id,
        "agent",
        "agent",
        "agent",
        answer,
        created_at,
        reply_to_user_id=user_id,
    )
    append_user_context(room_id, user_id, "agent", answer)

    await broadcast(
        room_id,
        {
            "type": "agent_typing",
            "user_id": user_id,
            "user_name": user_name,
            "active": False,
        },
    )
    await broadcast(
        room_id,
        {
            "type": "chat",
            "id": msg_id,
            "room_id": room_id,
            "user_id": "agent",
            "user_name": "agent",
            "role": "agent",
            "content": answer,
            "reply_to_user_id": user_id,
            "reply_to_user_name": user_name,
            "created_at": created_at,
        },
    )
