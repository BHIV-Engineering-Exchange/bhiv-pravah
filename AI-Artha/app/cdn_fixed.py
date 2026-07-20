#!/usr/bin/env python3
"""
Fixed CDN Routes - Handles video uploads properly
"""
import os
import time
import secrets
import hashlib
import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from fastapi.responses import FileResponse

try:
    from .auth import get_current_user_required, get_current_user_optional
except ImportError:
    async def get_current_user_required(request):
        class User:
            user_id = "demo001"
            username = "demo"
        return User()
    
    async def get_current_user_optional(request):
        return None

from core.database import DatabaseManager, db
from core.mongodb import get_collection

# Simple in-memory token storage (use Redis in production)
upload_tokens = {}

router = APIRouter(prefix="/cdn", tags=["CDN & File Management"])

@router.get("/upload-url")
async def get_upload_url(
    request: Request,
    filename: str,
    content_type: str = "application/octet-stream",
    current_user = Depends(get_current_user_required)
):
    """Get upload URL - Fixed version that works with video files"""
    
    # Generate secure upload token
    upload_token = secrets.token_urlsafe(32)
    
    # Store token with expiry (1 hour)
    upload_tokens[upload_token] = {
        'user_id': current_user.user_id,
        'filename': filename,
        'content_type': content_type,
        'expires_at': time.time() + 3600,
        'used': False
    }
    
    # Clean expired tokens
    current_time = time.time()
    expired = [token for token, data in upload_tokens.items() if data['expires_at'] < current_time]
    for token in expired:
        del upload_tokens[token]
    
    return {
        "upload_url": f"/cdn/upload/{upload_token}",
        "method": "POST",
        "expires_in": 3600,
        "max_file_size_mb": 100,
        "upload_token": upload_token,
        "supported_types": ["video/mp4", "video/avi", "video/mov", "audio/mp3", "image/jpeg", "image/png", "text/plain"],
        "instructions": [
            "1. Use the upload_token directly in the URL path",
            "2. POST to /cdn/upload/{token} (replace {token} with upload_token)",
            "3. Use multipart/form-data",
            "4. File field name: 'file'",
            "5. Include your JWT token in Authorization header"
        ],
        "example": f"curl -X POST 'http://localhost:9000/cdn/upload/{upload_token}' -H 'Authorization: Bearer YOUR_TOKEN' -F 'file=@{filename}'"
    }

@router.post("/upload/{upload_token}")
async def upload_file(
    upload_token: str,
    request: Request,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user_required)
):
    """Upload file using upload token - Fixed for video files"""
    
    # Handle URL decoding issues - extract just the token part
    import urllib.parse
    
    # If token contains URL path, extract just the token
    if "/cdn/upload/" in upload_token:
        actual_token = upload_token.split("/cdn/upload/")[-1]
    else:
        actual_token = upload_token
    
    # URL decode the token
    decoded_token = urllib.parse.unquote(actual_token)
    
    print(f"DEBUG: Raw upload_token: {upload_token}")
    print(f"DEBUG: Extracted token: {actual_token}")
    print(f"DEBUG: Decoded token: {decoded_token}")
    print(f"DEBUG: Available tokens: {list(upload_tokens.keys())}")
    
    # Try different token variations
    token_to_use = None
    for candidate in [decoded_token, actual_token, upload_token]:
        if candidate in upload_tokens:
            token_to_use = candidate
            print(f"DEBUG: Using token: {candidate}")
            break
    
    if not token_to_use:
        print(f"DEBUG: No matching token found for any variation")
        token_to_use = decoded_token  # Use decoded as fallback
    
    # Validate token
    if token_to_use not in upload_tokens:
        print(f"DEBUG: Token {token_to_use} not found in available tokens")
        raise HTTPException(status_code=400, detail=f"Invalid upload token: {token_to_use}")
    
    token_data = upload_tokens[token_to_use]
    
    # Check expiry
    if time.time() > token_data['expires_at']:
        del upload_tokens[upload_token]
        raise HTTPException(status_code=400, detail="Upload token expired")
    
    # Check if already used
    if token_data['used']:
        raise HTTPException(status_code=400, detail="Upload token already used")
    
    # Verify user
    if token_data['user_id'] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Token belongs to different user")
    
    # Validate file type
    allowed_extensions = {'.mp4', '.avi', '.mov', '.mp3', '.wav', '.jpg', '.jpeg', '.png', '.txt', '.pdf'}
    allowed_mime_types = {
        'video/mp4', 'video/avi', 'video/quicktime', 'audio/mpeg', 'audio/wav', 
        'image/jpeg', 'image/png', 'text/plain', 'application/pdf'
    }
    
    if file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"File extension {ext} not allowed")
    
    # More flexible MIME type validation
    if file.content_type and file.content_type not in allowed_mime_types:
        # Allow if extension is valid (browser may send generic MIME type)
        if file.filename:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in allowed_extensions:
                raise HTTPException(status_code=400, detail=f"MIME type {file.content_type} not allowed")
    
    # Read and validate file
    file_content = await file.read()
    max_size = 100 * 1024 * 1024  # 100MB
    
    if len(file_content) > max_size:
        raise HTTPException(status_code=413, detail=f"File too large. Max: {max_size/1024/1024}MB")
    
    # Generate content ID
    content_hash = hashlib.sha256(file_content).hexdigest()[:12]
    content_id = f"{content_hash}_{int(time.time())}"
    
    # Save file locally with proper structure
    os.makedirs("uploads", exist_ok=True)
    safe_filename = ''.join(c for c in file.filename if c.isalnum() or c in '.-_') if file.filename else "file"
    file_path = f"uploads/{content_id}_{safe_filename}"
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Mark token as used
    upload_tokens[token_to_use]['used'] = True
    print(f"DEBUG: File uploaded successfully: {content_id}")
    print(f"DEBUG: File saved to: {file_path}")
    print(f"DEBUG: File size: {len(file_content)} bytes")
    
    # Save to MongoDB
    try:
        content_col = get_collection("content")
        content_doc = {
            "content_id": content_id,
            "uploader_id": current_user.user_id,
            "title": file.filename or "Uploaded file",
            "description": "File uploaded via CDN",
            "file_path": file_path,
            "content_type": file.content_type or 'application/octet-stream',
            "uploaded_at": time.time(),
            "authenticity_score": 0.8,
            "current_tags": ['uploaded', 'cdn'],
            "views": 0,
            "likes": 0,
            "shares": 0,
        }
        if content_col is not None:
            content_col.update_one(
                {"content_id": content_id},
                {"$set": content_doc},
                upsert=True,
            )
            print(f"Content saved to MongoDB: {content_id}")
        else:
            print(f"MongoDB not available - file saved locally only: {content_id}")
    except Exception as db_error:
        print(f"Database save failed: {db_error}")
    
    return {
        "status": "success",
        "content_id": content_id,
        "filename": file.filename,
        "file_size": len(file_content),
        "file_path": file_path,
        "content_type": file.content_type,
        "download_url": f"/cdn/download/{content_id}",
        "stream_url": f"/cdn/stream/{content_id}",
        "message": "File uploaded successfully"
    }

@router.get("/download/{content_id}")
async def download_file(
    content_id: str,
    request: Request,
    current_user = Depends(get_current_user_optional)
):
    """Download file by content ID - Fixed version"""
    
    try:
        # Get file path from MongoDB
        file_path = None
        title = None
        
        content_col = get_collection("content")
        if content_col is not None:
            doc = content_col.find_one({"content_id": content_id})
            if doc:
                file_path = doc.get("file_path")
                title = doc.get("title")
        
        if not file_path:
            raise HTTPException(status_code=404, detail="Content not found")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        return FileResponse(
            file_path,
            filename=title or os.path.basename(file_path),
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@router.get("/stream/{content_id}")
async def stream_file(
    content_id: str,
    request: Request,
    current_user = Depends(get_current_user_optional)
):
    """Stream file by content ID - Fixed for video streaming"""
    
    try:
        # Get file path from MongoDB
        file_path = None
        content_type = None
        
        content_col = get_collection("content")
        if content_col is not None:
            doc = content_col.find_one({"content_id": content_id})
            if doc:
                file_path = doc.get("file_path")
                content_type = doc.get("content_type")
        
        if not file_path:
            raise HTTPException(status_code=404, detail="Content not found")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        # Determine media type based on file extension if not in database
        if not content_type:
            ext = os.path.splitext(file_path)[1].lower()
            content_type_map = {
                '.mp4': 'video/mp4',
                '.avi': 'video/avi',
                '.mov': 'video/quicktime',
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.txt': 'text/plain',
                '.pdf': 'application/pdf'
            }
            content_type = content_type_map.get(ext, 'application/octet-stream')
        
        return FileResponse(
            file_path,
            media_type=content_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming failed: {str(e)}")

@router.get("/list")
async def list_files(
    request: Request,
    limit: int = 20,
    current_user = Depends(get_current_user_required)
):
    """List uploaded files for current user - Fixed version"""
    
    try:
        files = []
        
        content_col = get_collection("content")
        if content_col is not None:
            results = list(
                content_col.find({"uploader_id": current_user.user_id})
                .sort("uploaded_at", -1)
                .limit(limit)
            )
            
            for doc in results:
                files.append({
                    "content_id": doc.get("content_id"),
                    "filename": doc.get("title"),
                    "content_type": doc.get("content_type"),
                    "uploaded_at": doc.get("uploaded_at"),
                    "views": doc.get("views", 0),
                    "likes": doc.get("likes", 0),
                    "download_url": f"/cdn/download/{doc.get('content_id')}",
                    "stream_url": f"/cdn/stream/{doc.get('content_id')}"
                })
        
        return {
            "files": files,
            "total": len(files),
            "user_id": current_user.user_id,
            "storage": "local_with_database_backup"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List failed: {str(e)}")

@router.delete("/delete/{content_id}")
async def delete_file(
    content_id: str,
    request: Request,
    current_user = Depends(get_current_user_required)
):
    """Delete file by content ID - Fixed version"""
    
    try:
        # Get file info from MongoDB
        file_path = None
        uploader_id = None
        
        content_col = get_collection("content")
        if content_col is not None:
            doc = content_col.find_one({"content_id": content_id})
            if doc:
                file_path = doc.get("file_path")
                uploader_id = doc.get("uploader_id")
                # Delete from MongoDB
                content_col.delete_one({"content_id": content_id})
        
        if not file_path:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Check ownership
        if uploader_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not your file")
        
        # Delete file from disk
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as file_error:
            print(f"File deletion failed: {file_error}")
        
        return {
            "status": "success",
            "message": "File deleted successfully",
            "content_id": content_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@router.get("/info/{content_id}")
async def get_file_info(
    content_id: str,
    request: Request,
    current_user = Depends(get_current_user_optional)
):
    """Get file information - Fixed version"""
    
    try:
        # Get file info from MongoDB
        doc = None
        
        content_col = get_collection("content")
        if content_col is not None:
            doc = content_col.find_one({"content_id": content_id})
        
        if not doc:
            raise HTTPException(status_code=404, detail="Content not found")
        
        return {
            "content_id": doc.get("content_id"),
            "filename": doc.get("title"),
            "content_type": doc.get("content_type"),
            "uploaded_at": doc.get("uploaded_at"),
            "authenticity_score": doc.get("authenticity_score"),
            "tags": doc.get("current_tags"),
            "views": doc.get("views", 0),
            "likes": doc.get("likes", 0),
            "shares": doc.get("shares", 0),
            "uploader_id": doc.get("uploader_id"),
            "download_url": f"/cdn/download/{content_id}",
            "stream_url": f"/cdn/stream/{content_id}",
            "storage": "local_with_database_backup"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Info failed: {str(e)}")
