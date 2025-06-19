import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import User, get_current_user
from app.database import get_db
from app.schemas import UserAssetCreate, UserAssetResponse
from app.services import AssetService
from app.storage import storage

router = APIRouter()

@router.get("", response_model=List[UserAssetResponse])
async def list_assets(
    asset_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's assets"""
    assets = await AssetService.get_user_assets(
        db=db,
        user_id=uuid.UUID(current_user.id),
        asset_type=asset_type,
        limit=limit,
        offset=offset
    )
    return assets

@router.post("/upload", response_model=UserAssetResponse)
async def upload_asset(
    file: UploadFile,
    asset_type: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a new asset"""
    try:
        print(f"[UPLOAD_ASSET] Starting upload process...")
        print(f"[UPLOAD_ASSET] Received params: asset_type={asset_type}, description={description}")
        print(f"[UPLOAD_ASSET] File info: name={file.filename}, content_type={file.content_type}, size={file.size}")
        
        if not file.filename:
            print("[UPLOAD_ASSET] Error: No filename provided")
            raise HTTPException(
                status_code=400,
                detail="No filename provided"
            )
            
        # Generate unique filename
        file_ext = file.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = f"assets/{current_user.id}/{asset_type}/{unique_filename}"
        print(f"[UPLOAD_ASSET] Generated file path: {file_path}")
        
        # Upload file to storage
        print("[UPLOAD_ASSET] Attempting to upload file to storage...")
        file_url = await storage.upload_file(
            file=file,
            path=file_path,
            bucket="assets"
        )
        
        if not file_url:
            print("[UPLOAD_ASSET] Error: Failed to get file URL from storage")
            raise HTTPException(
                status_code=500,
                detail="Failed to upload file to storage"
            )
        
        print(f"[UPLOAD_ASSET] File uploaded successfully, URL: {file_url}")
        
        # Create asset record
        print("[UPLOAD_ASSET] Creating asset record in database...")
        asset_data = UserAssetCreate(
            asset_type=asset_type,
            file_path=file_path,
            original_filename=file.filename,
            size=file.size or 0,  # Default to 0 if size is None
            mime_type=file.content_type or 'application/octet-stream',  # Default if content_type is None
            description=description
        )
        print(f"[UPLOAD_ASSET] Asset data prepared: {asset_data}")
        
        asset = await AssetService.create_asset(
            db=db,
            user_id=uuid.UUID(current_user.id),
            asset_data=asset_data
        )
        print("[UPLOAD_ASSET] Asset record created successfully")
        
        return asset
    except ValidationError as ve:
        print(f"[UPLOAD_ASSET] Validation error: {str(ve)}")
        raise HTTPException(
            status_code=422,
            detail=f"Validation error: {str(ve)}"
        )
    except Exception as e:
        print(f"[UPLOAD_ASSET] Unexpected error: {str(e)}")
        print(f"[UPLOAD_ASSET] Error type: {type(e)}")
        import traceback
        print(f"[UPLOAD_ASSET] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to upload asset: {str(e)}"
        )

@router.get("/{asset_id}", response_model=UserAssetResponse)
async def get_asset(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get asset by ID"""
    asset = await AssetService.get_asset(db=db, asset_id=asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    if asset.user_id != uuid.UUID(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access this asset")
    return asset

@router.get("/{asset_id}/download")
async def download_asset(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download an asset file"""
    asset = await AssetService.get_asset(db=db, asset_id=asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    if asset.user_id != uuid.UUID(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access this asset")
    
    # Download file from storage
    file_content = storage.download_file(asset.file_path, "assets")
    if not file_content:
        raise HTTPException(status_code=404, detail="File not found in storage")
    
    return Response(
        content=file_content,
        media_type=asset.mime_type,
        headers={
            "Content-Disposition": f"attachment; filename={asset.original_filename}"
        }
    ) 