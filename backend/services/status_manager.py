from typing import Dict, List, Any
import asyncio
from fastapi import WebSocket

class ScrapeStatusManager:
    _instance = None
    
    def __init__(self):
        # Store active connections: product_id -> List[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store latest status: product_id -> Dict
        self.latest_status: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ScrapeStatusManager()
        return cls._instance

    async def connect(self, websocket: WebSocket, product_id: str):
        await websocket.accept()
        if product_id not in self.active_connections:
            self.active_connections[product_id] = []
        self.active_connections[product_id].append(websocket)
        
        # Send latest status immediately if exists
        if product_id in self.latest_status:
            await websocket.send_json(self.latest_status[product_id])

    def disconnect(self, websocket: WebSocket, product_id: str):
        if product_id in self.active_connections:
            if websocket in self.active_connections[product_id]:
                self.active_connections[product_id].remove(websocket)

    async def broadcast_status(self, product_id: str, status: str, progress: int, message: str):
        """
        Broadcast updates to all connected clients for this product.
        """
        payload = {
            "status": status,    # 'running', 'completed', 'failed'
            "progress": progress, # 0-100
            "message": message
        }
        self.latest_status[product_id] = payload
        
        if product_id in self.active_connections:
            for connection in self.active_connections[product_id]:
                try:
                    await connection.send_json(payload)
                except Exception:
                    # Connection likely dead, remove it later or ignore
                    pass

status_manager = ScrapeStatusManager.get_instance()
