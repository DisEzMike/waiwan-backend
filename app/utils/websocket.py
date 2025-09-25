from typing import Dict, List
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Store active connections: {user_id: {room_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # Store room participants: {room_id: [user_ids]}
        self.room_participants: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, room_id: str):
        """Connect a user to a chat room"""
        await websocket.accept()
        
        # Initialize user connections if not exists
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        
        # Store connection
        self.active_connections[user_id][room_id] = websocket
        
        # Add user to room participants
        if room_id not in self.room_participants:
            self.room_participants[room_id] = []
        if user_id not in self.room_participants[room_id]:
            self.room_participants[room_id].append(user_id)
        
        logger.info(f"User {user_id} connected to room {room_id}")
        
        # Notify other participants that user is online
        await self.broadcast_to_room(room_id, {
            "type": "user_online",
            "user_id": user_id
        }, exclude_user=user_id)

    def disconnect(self, user_id: str, room_id: str):
        """Disconnect a user from a chat room"""
        try:
            if user_id in self.active_connections and room_id in self.active_connections[user_id]:
                del self.active_connections[user_id][room_id]
                
                # Clean up empty user connections
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # Remove user from room participants
            if room_id in self.room_participants and user_id in self.room_participants[room_id]:
                self.room_participants[room_id].remove(user_id)
                
                # Clean up empty rooms
                if not self.room_participants[room_id]:
                    del self.room_participants[room_id]
            
            logger.info(f"User {user_id} disconnected from room {room_id}")
        except Exception as e:
            logger.error(f"Error disconnecting user {user_id} from room {room_id}: {e}")

    async def send_personal_message(self, message: dict, user_id: str, room_id: str):
        """Send message to a specific user in a room"""
        try:
            if (user_id in self.active_connections and 
                room_id in self.active_connections[user_id]):
                websocket = self.active_connections[user_id][room_id]
                await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message to user {user_id} in room {room_id}: {e}")
            # Clean up broken connection
            self.disconnect(user_id, room_id)

    async def broadcast_to_room(self, room_id: str, message: dict, exclude_user: str = None):
        """Broadcast message to all participants in a room"""
        if room_id not in self.room_participants:
            return
        
        participants = self.room_participants[room_id].copy()
        for user_id in participants:
            if exclude_user and user_id == exclude_user:
                continue
            await self.send_personal_message(message, user_id, room_id)

    async def send_typing_indicator(self, room_id: str, user_id: str, is_typing: bool):
        """Send typing indicator to other participants"""
        message = {
            "type": "typing_indicator",
            "user_id": user_id,
            "is_typing": is_typing
        }
        await self.broadcast_to_room(room_id, message, exclude_user=user_id)

    def get_online_users_in_room(self, room_id: str) -> List[str]:
        """Get list of online users in a room"""
        if room_id not in self.room_participants:
            return []
        return self.room_participants[room_id].copy()

    def is_user_online_in_room(self, user_id: str, room_id: str) -> bool:
        """Check if user is online in a specific room"""
        return (user_id in self.active_connections and 
                room_id in self.active_connections[user_id])

# Global connection manager instance
manager = ConnectionManager()