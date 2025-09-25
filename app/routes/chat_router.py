from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy import and_, select, desc, func
from sqlalchemy.orm import Session
import json
import logging

from ..database.models.chats import ChatRooms, ChatMessages
from ..database.models.jobs import Jobs
from ..database.models.users import Users
from ..database.models.senior_users import SeniorUsers
from ..utils.deps import get_current_user, get_db
from ..utils.schemas import ChatMessageCreate, ChatMessageOut, ChatRoomOut, ChatRoomWithMessages
from ..utils.websocket import manager
from ..utils.jwt import decode_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

async def get_user_from_token(token: str, session: Session):
    """Get user from JWT token for WebSocket authentication"""
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        role = payload.get("role")
        
        if not user_id or not role:
            return None
            
        if role == "user":
            user = session.get(Users, user_id)
        elif role == "senior_user":
            user = session.get(SeniorUsers, user_id)
        else:
            return None
            
        if user:
            user.role = role
        return user
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return None

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """WebSocket endpoint for real-time chat"""
    # Get token from query parameters
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    
    # Get database session for initial validation
    from ..database.db import db as DBInstance
    user_id = None
    user_role = None
    user_displayname = None
    
    with DBInstance.session() as session:
        # Authenticate user
        user = await get_user_from_token(token, session)
        if not user:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        # Store user info for later use
        user_id = user.id
        user_role = user.role
        user_displayname = user.displayname
        
        # Check if room exists and user has access
        room = session.get(ChatRooms, room_id)
        if not room:
            await websocket.close(code=4004, reason="Room not found")
            return
        
        if room.user_id != user.id and room.senior_id != user.id:
            await websocket.close(code=4003, reason="Access denied")
            return
        
        if not room.is_active:
            await websocket.close(code=4003, reason="Room is not active")
            return
    
    # Connect user to room
    await manager.connect(websocket, user_id, room_id)
    
    try:
        while True:
            # Receive message from WebSocket
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle different message types
            message_type = message_data.get("type", "message")
            
            if message_type == "message":
                # Save message to database
                with DBInstance.session() as session:
                    message_content = message_data.get("message", "").strip()
                    if message_content:
                        # Create message record
                        new_message = ChatMessages(
                            room_id=room_id,
                            sender_id=user_id,
                            sender_type=user_role,
                            message=message_content,
                            is_read=False
                        )
                        session.add(new_message)
                        session.flush()
                        
                        # Prepare broadcast message
                        broadcast_message = {
                            "type": "new_message",
                            "message": {
                                "id": new_message.id,
                                "room_id": new_message.room_id,
                                "sender_id": new_message.sender_id,
                                "sender_type": new_message.sender_type,
                                "sender_name": user_displayname,
                                "message": new_message.message,
                                "is_read": new_message.is_read,
                                "created_at": new_message.created_at.isoformat()
                            }
                        }
                        
                        # Broadcast to all participants in room
                        await manager.broadcast_to_room(room_id, broadcast_message)
            
            elif message_type == "typing":
                # Handle typing indicator
                is_typing = message_data.get("is_typing", False)
                await manager.send_typing_indicator(room_id, user_id, is_typing)
            
            elif message_type == "mark_read":
                # Mark messages as read
                with DBInstance.session() as session:
                    if user_role == "user":
                        session.execute(
                            ChatMessages.__table__.update()
                            .where(and_(
                                ChatMessages.room_id == room_id,
                                ChatMessages.sender_type == "senior_user",
                                ChatMessages.is_read == False
                            ))
                            .values(is_read=True)
                        )
                    elif user_role == "senior_user":
                        session.execute(
                            ChatMessages.__table__.update()
                            .where(and_(
                                ChatMessages.room_id == room_id,
                                ChatMessages.sender_type == "user",
                                ChatMessages.is_read == False
                            ))
                            .values(is_read=True)
                        )
                    session.commit()
                    
                    # Notify other participants about read status
                    await manager.broadcast_to_room(room_id, {
                        "type": "messages_read",
                        "user_id": user_id
                    }, exclude_user=user_id)
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id} in room {room_id}: {e}")
    finally:
        # Disconnect user from room
        manager.disconnect(user_id, room_id)
        # Notify other participants that user is offline
        await manager.broadcast_to_room(room_id, {
            "type": "user_offline",
            "user_id": user_id
        })

async def create_chat_room_if_not_exists(job_id: int, session: Session) -> ChatRooms:
    """Create chat room when job status becomes 1"""
    # Check if job exists and status is 1
    job = session.get(Jobs, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    
    if job.status != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chat only available when job status is 1")
    
    # Check if chat room already exists
    existing_room = session.execute(
        select(ChatRooms).where(ChatRooms.job_id == job_id)
    ).scalars().first()
    
    if existing_room:
        return existing_room
    
    # Create new chat room
    chat_room = ChatRooms(
        job_id=job_id,
        user_id=job.user_id,
        senior_id=job.senior_id,
        is_active=True
    )
    session.add(chat_room)
    session.flush()
    return chat_room

@router.get("/rooms", response_model=List[ChatRoomOut])
async def get_my_chat_rooms(ctx = Depends(get_current_user), session: Session = Depends(get_db)):
    """Get all chat rooms for current user"""
    user, _, _ = ctx
    
    if user.role == "user":
        stmt = select(ChatRooms).where(
            and_(ChatRooms.user_id == user.id, ChatRooms.is_active == True)
        ).order_by(desc(ChatRooms.created_at))
    elif user.role == "senior_user":
        stmt = select(ChatRooms).where(
            and_(ChatRooms.senior_id == user.id, ChatRooms.is_active == True)
        ).order_by(desc(ChatRooms.created_at))
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user role")
    
    rooms = session.scalars(stmt).all()
    
    # Build response with additional info
    room_responses = []
    for room in rooms:
        # Get user and senior names
        room_user = session.get(Users, room.user_id)
        room_senior = session.get(SeniorUsers, room.senior_id)
        
        # Get unread message count
        unread_count = session.scalar(
            select(func.count(ChatMessages.id))
            .where(and_(
                ChatMessages.room_id == room.id,
                ChatMessages.sender_id != user.id,
                ChatMessages.is_read == False
            ))
        ) or 0
        
        # Get last message
        last_message_stmt = (
            select(ChatMessages)
            .where(ChatMessages.room_id == room.id)
            .order_by(desc(ChatMessages.created_at))
            .limit(1)
        )
        last_message = session.scalars(last_message_stmt).first()
        
        last_message_out = None
        if last_message:
            sender_name = room_user.displayname if last_message.sender_type == "user" else room_senior.displayname
            last_message_out = ChatMessageOut(
                id=last_message.id,
                room_id=last_message.room_id,
                sender_id=last_message.sender_id,
                sender_type=last_message.sender_type,
                sender_name=sender_name,
                message=last_message.message,
                is_read=last_message.is_read,
                created_at=last_message.created_at
            )
        
        room_responses.append(ChatRoomOut(
            id=room.id,
            job_id=room.job_id,
            user_id=room.user_id,
            senior_id=room.senior_id,
            user_name=room_user.displayname if room_user else None,
            senior_name=room_senior.displayname if room_senior else None,
            is_active=room.is_active,
            created_at=room.created_at,
            unread_count=unread_count,
            last_message=last_message_out
        ))
    
    return room_responses

@router.get("/rooms/{room_id}", response_model=ChatRoomWithMessages)
async def get_chat_room(room_id: str, ctx = Depends(get_current_user), session: Session = Depends(get_db)):
    """Get chat room with messages"""
    user, _, _ = ctx
    
    room = session.get(ChatRooms, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat room not found")
    
    # Check if user has access to this room
    if room.user_id != user.id and room.senior_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # Get messages
    messages_stmt = (
        select(ChatMessages)
        .where(ChatMessages.room_id == room_id)
        .order_by(ChatMessages.created_at)
    )
    messages = session.scalars(messages_stmt).all()
    
    # Get user and senior names
    room_user = session.get(Users, room.user_id)
    room_senior = session.get(SeniorUsers, room.senior_id)
    
    # Build message responses
    message_responses = []
    for msg in messages:
        sender_name = room_user.displayname if msg.sender_type == "user" else room_senior.displayname
        message_responses.append(ChatMessageOut(
            id=msg.id,
            room_id=msg.room_id,
            sender_id=msg.sender_id,
            sender_type=msg.sender_type,
            sender_name=sender_name,
            message=msg.message,
            is_read=msg.is_read,
            created_at=msg.created_at
        ))
    
    # Mark messages as read for current user
    if user.role == "user":
        session.execute(
            ChatMessages.__table__.update()
            .where(and_(
                ChatMessages.room_id == room_id,
                ChatMessages.sender_type == "senior_user",
                ChatMessages.is_read == False
            ))
            .values(is_read=True)
        )
    elif user.role == "senior_user":
        session.execute(
            ChatMessages.__table__.update()
            .where(and_(
                ChatMessages.room_id == room_id,
                ChatMessages.sender_type == "user",
                ChatMessages.is_read == False
            ))
            .values(is_read=True)
        )
    
    session.commit()
    
    return ChatRoomWithMessages(
        id=room.id,
        job_id=room.job_id,
        user_id=room.user_id,
        senior_id=room.senior_id,
        user_name=room_user.displayname if room_user else None,
        senior_name=room_senior.displayname if room_senior else None,
        is_active=room.is_active,
        created_at=room.created_at,
        messages=message_responses
    )

@router.post("/rooms/{room_id}/messages", response_model=ChatMessageOut)
async def send_message(
    room_id: str,
    payload: ChatMessageCreate,
    ctx = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """Send a message to chat room (REST API - also works with WebSocket)"""
    user, _, _ = ctx
    
    room = session.get(ChatRooms, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat room not found")
    
    # Check if user has access to this room
    if room.user_id != user.id and room.senior_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    if not room.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chat room is not active")
    
    # Create message
    message = ChatMessages(
        room_id=room_id,
        sender_id=user.id,
        sender_type=user.role,
        message=payload.message.strip(),
        is_read=False
    )
    
    session.add(message)
    session.flush()
    
    # Get sender name
    sender_name = user.displayname
    
    message_out = ChatMessageOut(
        id=message.id,
        room_id=message.room_id,
        sender_id=message.sender_id,
        sender_type=message.sender_type,
        sender_name=sender_name,
        message=message.message,
        is_read=message.is_read,
        created_at=message.created_at
    )
    
    # Broadcast to WebSocket connections
    broadcast_message = {
        "type": "new_message",
        "message": {
            "id": message.id,
            "room_id": message.room_id,
            "sender_id": message.sender_id,
            "sender_type": message.sender_type,
            "sender_name": sender_name,
            "message": message.message,
            "is_read": message.is_read,
            "created_at": message.created_at.isoformat()
        }
    }
    await manager.broadcast_to_room(room_id, broadcast_message)
    
    return message_out

@router.post("/jobs/{job_id}/room", response_model=ChatRoomOut)
async def create_or_get_chat_room(job_id: int, ctx = Depends(get_current_user), session: Session = Depends(get_db)):
    """Create or get chat room for a job (when status is 1)"""
    user, _, _ = ctx
    
    # Create or get chat room
    room = await create_chat_room_if_not_exists(job_id, session)
    
    # Check if user has access
    if room.user_id != user.id and room.senior_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # Get user and senior names
    room_user = session.get(Users, room.user_id)
    room_senior = session.get(SeniorUsers, room.senior_id)
    
    return ChatRoomOut(
        id=room.id,
        job_id=room.job_id,
        user_id=room.user_id,
        senior_id=room.senior_id,
        user_name=room_user.displayname if room_user else None,
        senior_name=room_senior.displayname if room_senior else None,
        is_active=room.is_active,
        created_at=room.created_at
    )

@router.get("/rooms/{room_id}/online-users")
async def get_online_users(room_id: str, ctx = Depends(get_current_user), session: Session = Depends(get_db)):
    """Get list of online users in a chat room"""
    user, _, _ = ctx
    
    room = session.get(ChatRooms, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat room not found")
    
    # Check if user has access
    if room.user_id != user.id and room.senior_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # Get online users
    online_user_ids = manager.get_online_users_in_room(room_id)
    
    # Get user details
    online_users = []
    for user_id in online_user_ids:
        if user_id == room.user_id:
            user_obj = session.get(Users, user_id)
            if user_obj:
                online_users.append({
                    "id": user_id,
                    "name": user_obj.displayname,
                    "type": "user"
                })
        elif user_id == room.senior_id:
            senior_obj = session.get(SeniorUsers, user_id)
            if senior_obj:
                online_users.append({
                    "id": user_id,
                    "name": senior_obj.displayname,
                    "type": "senior_user"
                })
    
    return {"online_users": online_users}