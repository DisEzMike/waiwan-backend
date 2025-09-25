from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy import update
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from pathlib import Path

from ..utils.deps import get_current_user, get_db
from ..utils.schemas import FileUploadResponse, FileOut
from ..utils.file_upload import (
    validate_file, save_uploaded_file, delete_file, get_file_url, 
    FileUploadError, UPLOAD_DIR
)
from ..database.models.files import Files
from ..database.models.users import UserProfiles
from ..database.models.senior_users import SeniorProfiles

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    is_profile_image: bool = Query(False, description="Set as profile image"),
    db: Session = Depends(get_db),
    auth_data = Depends(get_current_user)
):
    """Upload a file"""
    try:
        # Extract user from auth_data tuple (user, profile, ability)
        current_user = auth_data[0]
        
        # Validate file
        validate_file(file)
        
        # Save file
        file_path, content, file_hash = await save_uploaded_file(file, current_user.id)
        
        # Create file record
        db_file = Files(
            filename=Path(file_path).name,
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            content_type=file.content_type,
            file_hash=file_hash,
            upload_by=current_user.id,
            is_active=True
        )
        
        db.add(db_file)
        db.flush()  # Get the ID
        
        print(is_profile_image, db_file.id)
        
        # If it's a profile image, update user profile
        if is_profile_image and file.content_type.startswith('image/'):
            if current_user.role == 'user':
                user_profile = db.get(UserProfiles, current_user.profile_id)
                if user_profile:
                    # Deactivate old profile image if exists
                    if user_profile.profile_image_id:
                        old_file = db.get(Files, user_profile.profile_image_id)
                        if old_file:
                            old_file.is_active = False
                            await delete_file(old_file.file_path)
                    
                    user_profile.profile_image_id = db_file.id
                    # stmt = (
                    #     update(UserProfiles).where(UserProfiles.id == user_profile.id).
                    #     values(profile_image_id=db_file.id)
                    # )
                    # db.execute(stmt)
            
            elif current_user.role == 'senior_user':
                senior_profile = db.get(SeniorProfiles, current_user.id)
                if senior_profile:
                    # Deactivate old profile image if exists
                    if senior_profile.profile_image_id:
                        old_file = db.get(Files, senior_profile.profile_image_id)
                        if old_file:
                            old_file.is_active = False
                            await delete_file(old_file.file_path)
                    
                    senior_profile.profile_image_id = db_file.id
        
        db.commit()
        
        # Generate file URL
        file_url = get_file_url(file_path)
        
        return FileUploadResponse(
            id=db_file.id,
            filename=db_file.filename,
            original_filename=db_file.original_filename,
            file_path=file_path,
            file_size=db_file.file_size,
            content_type=db_file.content_type,
            upload_url=file_url,
            created_at=db_file.created_at,
            is_profile_image=is_profile_image
        )
        
    except FileUploadError as e:
        db.rollback()
        # Clean up file if it was saved
        if 'file_path' in locals():
            await delete_file(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(e)
        db.rollback()
        if 'file_path' in locals():
            await delete_file(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error uploading file"
        )

@router.get("/user/my-files", response_model=List[FileOut])
async def get_my_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    auth_data = Depends(get_current_user)
):
    """Get current user's files"""
    from sqlalchemy import select
    
    current_user = auth_data[0]  # Extract user from tuple
    
    query = select(Files).filter(
        Files.upload_by == current_user.id,
        Files.is_active == True
    ).order_by(Files.created_at.desc()).offset(skip).limit(limit)
    
    result = db.execute(query)
    files = result.scalars().all()
    
    return [
        FileOut(
            id=file.id,
            filename=file.filename,
            original_filename=file.original_filename,
            file_size=file.file_size,
            content_type=file.content_type,
            file_url=get_file_url(file.file_path),
            upload_date=file.created_at,
            is_active=file.is_active
        )
        for file in files
    ]

@router.get("/{file_id}", response_model=FileOut)
async def get_file_info(
    file_id: int,
    db: Session = Depends(get_db),
    auth_data = Depends(get_current_user)
):
    """Get file information"""
    current_user = auth_data[0]  # Extract user from tuple
    
    file_record = db.get(Files, file_id)
    
    if not file_record or not file_record.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check if user can access file (owner or file is public profile image)
    can_access = (
        file_record.upload_by == current_user.id or
        _is_profile_image(db, file_id)
    )
    
    if not can_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    file_url = get_file_url(file_record.file_path)
    
    return FileOut(
        id=file_record.id,
        filename=file_record.filename,
        original_filename=file_record.original_filename,
        file_size=file_record.file_size,
        content_type=file_record.content_type,
        file_url=file_url,
        upload_date=file_record.created_at,
        is_active=file_record.is_active
    )

@router.get("/{category}/{filename}")
async def download_file(
    category: str,
    filename: str,
    db: Session = Depends(get_db)
):
    """Download/serve file"""
    file_path = UPLOAD_DIR / category / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Get file record for validation
    from sqlalchemy import select
    
    file_query = select(Files).filter(
        Files.file_path == str(file_path),
        Files.is_active == True
    )
    result = db.execute(file_query)
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or inactive"
        )
    
    return FileResponse(
        path=file_path,
        filename=file_record.original_filename,
        media_type=file_record.content_type
    )


@router.delete("/{file_id}")
async def delete_file_endpoint(
    file_id: int,
    db: Session = Depends(get_db),
    auth_data = Depends(get_current_user)
):
    """Delete a file"""
    current_user = auth_data[0]  # Extract user from tuple
    
    file_record = db.get(Files, file_id)
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check ownership
    if file_record.upload_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if it's being used as profile image
    is_profile = _is_profile_image(db, file_id)
    if is_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete file being used as profile image"
        )
    
    # Mark as inactive and delete physical file
    file_record.is_active = False
    await delete_file(file_record.file_path)
    db.commit()
    
    return {"message": "File deleted successfully"}

def _is_profile_image(db: Session, file_id: int) -> bool:
    """Check if file is being used as a profile image"""
    from sqlalchemy import select, or_
    
    # Check UserProfiles
    user_query = select(UserProfiles).filter(UserProfiles.profile_image_id == file_id)
    user_result = db.execute(user_query)
    if user_result.first():
        return True
    
    # Check SeniorProfiles
    senior_query = select(SeniorProfiles).filter(SeniorProfiles.profile_image_id == file_id)
    senior_result = db.execute(senior_query)
    if senior_result.first():
        return True
    
    return False