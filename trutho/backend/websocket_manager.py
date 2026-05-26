import json
from typing import List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, event_type: str, data: dict):
        message = json.dumps({"type": event_type, "data": data})
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.disconnect(d)

    async def broadcast_new_post(self, post_data: dict):
        await self.broadcast("new_post", post_data)

    async def broadcast_new_comment(self, comment_data: dict):
        await self.broadcast("new_comment", comment_data)

    async def broadcast_reaction(self, post_id: int, likes: int, dislikes: int):
        await self.broadcast("reaction_update", {
            "post_id": post_id,
            "likes": likes,
            "dislikes": dislikes
        })

    async def broadcast_trending(self, trending_data: list):
        await self.broadcast("trending_update", {"posts": trending_data})


manager = ConnectionManager()
