import os
from typing import BinaryIO, Optional

from fastapi import UploadFile
from supabase import Client, create_client

from app.config import settings


class StorageService:
    """Service for handling file storage using Supabase Storage"""
    
    def __init__(self) -> None:
        if not settings.SUPABASE_URL:
            raise ValueError("SUPABASE_URL is required")
        if not settings.SUPABASE_KEY:
            raise ValueError("SUPABASE_KEY (service role key) is required for storage operations")
            
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        self._ensure_buckets_exist()
    
    def _ensure_buckets_exist(self) -> None:
        """Ensure required storage buckets exist"""
        required_buckets = ['assets']
        existing_buckets = self.supabase.storage.list_buckets()
        existing_bucket_names = [b.name for b in existing_buckets]
        
        for bucket in required_buckets:
            if bucket not in existing_bucket_names:
                try:
                    self.supabase.storage.create_bucket(bucket)
                except Exception as e:
                    print(f"Warning: Failed to create bucket {bucket}: {e}")
    
    async def upload_file(
        self,
        file: UploadFile,
        path: str,
        bucket: str = "assets"
    ) -> Optional[str]:
        """
        Upload a file to storage
        
        Args:
            file: The file to upload
            path: The path within the bucket where the file should be stored
            bucket: The bucket to store the file in
            
        Returns:
            The public URL of the uploaded file, or None if upload failed
        """
        try:
            # Read file content
            content = await file.read()
            
            # Upload to Supabase Storage
            result = self.supabase.storage.from_(bucket).upload(
                path,
                content,
                file_options={"contentType": file.content_type}
            )
            
            # Get public URL
            if result:
                return self.supabase.storage.from_(bucket).get_public_url(path)
            
            return None
            
        except Exception as e:
            print(f"Failed to upload file: {e}")
            return None
    
    def download_file(self, path: str, bucket: str = "assets") -> Optional[bytes]:
        """
        Download a file from storage
        
        Args:
            path: The path of the file to download
            bucket: The bucket containing the file
            
        Returns:
            The file content as bytes, or None if download failed
        """
        try:
            # Download from Supabase Storage
            result = self.supabase.storage.from_(bucket).download(path)
            return result
            
        except Exception as e:
            print(f"Failed to download file: {e}")
            return None
    
    def get_file_url(self, path: str, bucket: str = "assets") -> Optional[str]:
        """
        Get the public URL of a file
        
        Args:
            path: The path of the file
            bucket: The bucket containing the file
            
        Returns:
            The public URL of the file, or None if failed
        """
        try:
            return self.supabase.storage.from_(bucket).get_public_url(path)
        except Exception as e:
            print(f"Failed to get file URL: {e}")
            return None
    
    def delete_file(self, path: str, bucket: str = "assets") -> bool:
        """
        Delete a file from storage
        
        Args:
            path: The path of the file to delete
            bucket: The bucket containing the file
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            self.supabase.storage.from_(bucket).remove(path)
            return True
        except Exception as e:
            print(f"Failed to delete file: {e}")
            return False

# Create a global instance
storage = StorageService() 