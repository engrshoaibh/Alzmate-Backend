# cloudinary_service.py
import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import Optional
from pathlib import Path
import requests
from config import (
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET,
    CLOUDINARY_UPLOAD_PRESET
)

# Configure Cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

def upload_audio_file(
    file_path: str,
    user_id: str,
    entry_id: Optional[str] = None,
    folder: Optional[str] = None
) -> str:
    """
    Upload audio file to Cloudinary.
    
    Args:
        file_path: Path to the audio file
        user_id: User ID for folder organization
        entry_id: Optional entry ID for folder organization
        folder: Optional custom folder path
    
    Returns:
        Secure URL of the uploaded file
    """
    try:
        # Determine folder path
        if folder:
            upload_folder = folder
        elif entry_id:
            upload_folder = f"journal/{user_id}/{entry_id}"
        else:
            upload_folder = f"journal/{user_id}"
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            file_path,
            resource_type="video",  # Audio files use video resource type in Cloudinary
            folder=upload_folder,
            upload_preset=CLOUDINARY_UPLOAD_PRESET,
            use_filename=True,
            unique_filename=True
        )
        
        return result.get("secure_url", result.get("url"))
    except Exception as e:
        raise Exception(f"Failed to upload audio file: {str(e)}")

def upload_audio_from_bytes(
    audio_bytes: bytes,
    filename: str,
    user_id: str,
    entry_id: Optional[str] = None,
    folder: Optional[str] = None
) -> str:
    """
    Upload audio file from bytes to Cloudinary.
    
    Args:
        audio_bytes: Audio file as bytes
        filename: Original filename
        user_id: User ID for folder organization
        entry_id: Optional entry ID for folder organization
        folder: Optional custom folder path
    
    Returns:
        Secure URL of the uploaded file
    """
    try:
        # Determine folder path
        if folder:
            upload_folder = folder
        elif entry_id:
            upload_folder = f"journal/{user_id}/{entry_id}"
        else:
            upload_folder = f"journal/{user_id}"
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            audio_bytes,
            resource_type="video",  # Audio files use video resource type
            folder=upload_folder,
            upload_preset=CLOUDINARY_UPLOAD_PRESET,
            public_id=filename,
            use_filename=True,
            unique_filename=True
        )
        
        return result.get("secure_url", result.get("url"))
    except Exception as e:
        raise Exception(f"Failed to upload audio file: {str(e)}")

def upload_file_from_url(
    file_url: str,
    user_id: str,
    entry_id: Optional[str] = None,
    folder: Optional[str] = None
) -> str:
    """
    Upload a file from a URL to Cloudinary.
    
    Args:
        file_url: URL of the file to upload
        user_id: User ID for folder organization
        entry_id: Optional entry ID for folder organization
        folder: Optional custom folder path
    
    Returns:
        Secure URL of the uploaded file
    """
    try:
        # Download file from URL
        response = requests.get(file_url)
        response.raise_for_status()
        
        # Determine folder path
        if folder:
            upload_folder = folder
        elif entry_id:
            upload_folder = f"journal/{user_id}/{entry_id}"
        else:
            upload_folder = f"journal/{user_id}"
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            response.content,
            resource_type="video",  # Audio files use video resource type
            folder=upload_folder,
            upload_preset=CLOUDINARY_UPLOAD_PRESET,
            use_filename=True,
            unique_filename=True
        )
        
        return result.get("secure_url", result.get("url"))
    except Exception as e:
        raise Exception(f"Failed to upload file from URL: {str(e)}")

def delete_file(public_id: str) -> bool:
    """
    Delete a file from Cloudinary.
    
    Args:
        public_id: Public ID of the file to delete
    
    Returns:
        True if successful, False otherwise
    """
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type="video")
        return result.get("result") == "ok"
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False

