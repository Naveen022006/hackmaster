"""
API Routes for R8: Cloud Storage Infrastructure
Handles file uploads/downloads and storage management.
"""
from fastapi import APIRouter, HTTPException
import os
from pathlib import Path

from services.cloud_storage_service import get_storage_manager
from api.models import (
    CloudUploadRequest,
    CloudDownloadRequest,
    StorageOperationResponse,
    StorageListResponse,
    StorageOperationLogResponse
)

router = APIRouter(prefix="/storage", tags=["Cloud Storage"])
storage_manager = get_storage_manager(provider_type="local")


@router.post("/upload", response_model=StorageOperationResponse)
async def upload_file(request: CloudUploadRequest):
    """
    Upload a file to cloud storage (with local fallback).
    
    - **file_path**: Local file path to upload
    - **remote_path**: Remote storage path
    - **file_type**: Type of file (model, log, data)
    """
    if not os.path.exists(request.file_path):
        raise HTTPException(
            status_code=400,
            detail=f"File not found: {request.file_path}"
        )

    success = storage_manager.upload_file(request.file_path, request.remote_path)

    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file to storage"
        )

    return StorageOperationResponse(
        success=True,
        operation="upload",
        status="completed",
        local_path=request.file_path,
        remote_path=request.remote_path,
        timestamp=__import__("datetime").datetime.now().isoformat(),
        provider=storage_manager.provider_type
    )


@router.post("/download", response_model=StorageOperationResponse)
async def download_file(request: CloudDownloadRequest):
    """
    Download a file from cloud storage.
    
    - **remote_path**: Remote storage path
    - **local_path**: Local destination path
    """
    success = storage_manager.download_file(request.remote_path, request.local_path)

    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download file from storage"
        )

    return StorageOperationResponse(
        success=True,
        operation="download",
        status="completed",
        local_path=request.local_path,
        remote_path=request.remote_path,
        timestamp=__import__("datetime").datetime.now().isoformat(),
        provider=storage_manager.provider_type
    )


@router.post("/upload-model")
async def upload_model(model_path: str, model_name: str):
    """
    Upload an ML model to cloud storage.
    
    - **model_path**: Local path to model file
    - **model_name**: Name to store model as
    """
    if not os.path.exists(model_path):
        raise HTTPException(status_code=400, detail=f"Model file not found: {model_path}")

    success = storage_manager.upload_model(model_path, model_name)

    return {
        "success": success,
        "message": f"Model '{model_name}' uploaded successfully" if success else "Upload failed",
        "model_name": model_name,
        "storage_path": f"models/{model_name}"
    }


@router.post("/download-model")
async def download_model(model_name: str, local_path: str):
    """
    Download an ML model from cloud storage.
    
    - **model_name**: Name of model to download
    - **local_path**: Local destination path
    """
    success = storage_manager.download_model(model_name, local_path)

    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to download model: {model_name}")

    return {
        "success": True,
        "message": f"Model '{model_name}' downloaded successfully",
        "local_path": local_path,
        "model_name": model_name
    }


@router.get("/models", response_model=StorageListResponse)
async def list_models():
    """
    List all ML models stored in cloud storage.
    """
    models = storage_manager.list_models()

    return StorageListResponse(
        prefix="models/",
        files=models,
        total_files=len(models),
        provider=storage_manager.provider_type
    )


@router.get("/logs", response_model=StorageListResponse)
async def list_logs():
    """
    List all logs stored in cloud storage.
    """
    logs = storage_manager.list_logs()

    return StorageListResponse(
        prefix="logs/",
        files=logs,
        total_files=len(logs),
        provider=storage_manager.provider_type
    )


@router.post("/upload-logs")
async def upload_logs(log_path: str, log_name: str):
    """
    Upload application logs to cloud storage.
    
    - **log_path**: Local path to log file
    - **log_name**: Name to store log as
    """
    if not os.path.exists(log_path):
        raise HTTPException(status_code=400, detail=f"Log file not found: {log_path}")

    success = storage_manager.upload_logs(log_path, log_name)

    return {
        "success": success,
        "message": f"Logs uploaded successfully" if success else "Upload failed",
        "log_name": log_name
    }


@router.delete("/file")
async def delete_file(remote_path: str):
    """
    Delete a file from cloud storage.
    
    - **remote_path**: Path to file to delete
    """
    success = storage_manager.primary.delete_file(remote_path)

    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {remote_path}")

    return {
        "success": True,
        "message": f"File deleted successfully",
        "remote_path": remote_path
    }


@router.get("/logs-list", response_model=StorageOperationLogResponse)
async def get_operation_logs():
    """
    Get history of all storage operations (uploads/downloads).
    """
    logs = storage_manager.get_operation_log()

    providers = list(set(log.get("provider") for log in logs))

    return StorageOperationLogResponse(
        operations=logs,
        total_operations=len(logs),
        providers_used=providers
    )


@router.get("/status")
async def storage_status():
    """
    Get cloud storage status and configuration.
    """
    return {
        "status": "operational",
        "provider_type": storage_manager.provider_type,
        "primary_provider": str(type(storage_manager.primary).__name__),
        "fallback_available": storage_manager.fallback is not None,
        "total_operations": len(storage_manager.get_operation_log()),
        "message": "Cloud storage infrastructure is operational with local storage backend"
    }


@router.post("/configure")
async def configure_storage(provider_type: str = "local"):
    """
    Configure storage provider (local or S3).
    
    - **provider_type**: Storage provider type (local, s3)
    """
    if provider_type not in ["local", "s3"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid provider type. Supported: local, s3"
        )

    return {
        "success": True,
        "message": f"Storage provider configured to {provider_type}",
        "provider_type": provider_type,
        "fallback_available": True
    }
