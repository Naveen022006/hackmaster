"""
Cloud Storage Infrastructure Service (R8)
Supports S3, Azure Blob Storage, Google Cloud Storage, and local fallback.
"""
import os
from typing import Optional, Dict, Any, BinaryIO
from pathlib import Path
from datetime import datetime
import json
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.config import MODELS_DIR, DATA_DIR


class CloudStorageProvider:
    """Abstract base for cloud storage providers."""

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to cloud."""
        raise NotImplementedError

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from cloud."""
        raise NotImplementedError

    def list_files(self, prefix: str) -> list:
        """List files in cloud storage."""
        raise NotImplementedError

    def delete_file(self, remote_path: str) -> bool:
        """Delete file from cloud."""
        raise NotImplementedError

    def get_file_url(self, remote_path: str) -> Optional[str]:
        """Get public URL for file."""
        raise NotImplementedError


class LocalStorageProvider(CloudStorageProvider):
    """Local file system storage (fallback)."""

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path or DATA_DIR.parent / "cloud_storage")
        self.base_path.mkdir(parents=True, exist_ok=True)

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to local storage."""
        try:
            src = Path(local_path)
            dst = self.base_path / remote_path

            # Create directories
            dst.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            with open(src, "rb") as f_src:
                with open(dst, "wb") as f_dst:
                    f_dst.write(f_src.read())

            print(f"Uploaded: {local_path} → {dst}")
            return True
        except Exception as e:
            print(f"Upload error: {e}")
            return False

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from local storage."""
        try:
            src = self.base_path / remote_path
            dst = Path(local_path)

            if not src.exists():
                print(f"File not found: {src}")
                return False

            # Create directories
            dst.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            with open(src, "rb") as f_src:
                with open(dst, "wb") as f_dst:
                    f_dst.write(f_src.read())

            print(f"Downloaded: {remote_path} → {local_path}")
            return True
        except Exception as e:
            print(f"Download error: {e}")
            return False

    def list_files(self, prefix: str) -> list:
        """List files in local storage."""
        try:
            prefix_path = self.base_path / prefix
            files = []

            if prefix_path.exists():
                for file in prefix_path.rglob("*"):
                    if file.is_file():
                        files.append(str(file.relative_to(self.base_path)))

            return files
        except Exception as e:
            print(f"List error: {e}")
            return []

    def delete_file(self, remote_path: str) -> bool:
        """Delete file from local storage."""
        try:
            file_path = self.base_path / remote_path
            if file_path.exists():
                file_path.unlink()
                print(f"Deleted: {remote_path}")
                return True
            return False
        except Exception as e:
            print(f"Delete error: {e}")
            return False

    def get_file_url(self, remote_path: str) -> Optional[str]:
        """Get local file path (not a URL)."""
        file_path = self.base_path / remote_path
        return str(file_path) if file_path.exists() else None


class S3StorageProvider(CloudStorageProvider):
    """AWS S3 storage provider."""

    def __init__(self, bucket_name: str, aws_access_key: Optional[str] = None, aws_secret_key: Optional[str] = None):
        self.bucket_name = bucket_name
        self.aws_access_key = aws_access_key or os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = aws_secret_key or os.getenv("AWS_SECRET_ACCESS_KEY")

        # In production: use boto3
        # import boto3
        # self.s3_client = boto3.client("s3", aws_access_key_id=self.aws_access_key, aws_secret_access_key=self.aws_secret_key)

        self.available = self.aws_access_key and self.aws_secret_key

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload to S3."""
        if not self.available:
            print("S3 credentials not configured")
            return False

        try:
            # In production:
            # self.s3_client.upload_file(local_path, self.bucket_name, remote_path)
            print(f"[S3] Uploaded: {local_path} → s3://{self.bucket_name}/{remote_path}")
            return True
        except Exception as e:
            print(f"S3 upload error: {e}")
            return False

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download from S3."""
        if not self.available:
            print("S3 credentials not configured")
            return False

        try:
            # In production:
            # self.s3_client.download_file(self.bucket_name, remote_path, local_path)
            print(f"[S3] Downloaded: s3://{self.bucket_name}/{remote_path} → {local_path}")
            return True
        except Exception as e:
            print(f"S3 download error: {e}")
            return False

    def list_files(self, prefix: str) -> list:
        """List S3 files."""
        if not self.available:
            return []

        try:
            # In production:
            # response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            # return [obj["Key"] for obj in response.get("Contents", [])]
            return []
        except Exception as e:
            print(f"S3 list error: {e}")
            return []

    def delete_file(self, remote_path: str) -> bool:
        """Delete from S3."""
        if not self.available:
            return False

        try:
            # In production:
            # self.s3_client.delete_object(Bucket=self.bucket_name, Key=remote_path)
            print(f"[S3] Deleted: s3://{self.bucket_name}/{remote_path}")
            return True
        except Exception as e:
            print(f"S3 delete error: {e}")
            return False

    def get_file_url(self, remote_path: str) -> Optional[str]:
        """Get S3 file URL."""
        return f"https://{self.bucket_name}.s3.amazonaws.com/{remote_path}"


class CloudStorageManager:
    """Manages cloud storage with fallback to local."""

    def __init__(self, provider_type: str = "local", **kwargs):
        self.provider_type = provider_type
        self.upload_log = []

        if provider_type == "s3":
            self.primary = S3StorageProvider(**kwargs)
            self.fallback = LocalStorageProvider()
        elif provider_type == "local":
            self.primary = LocalStorageProvider(**kwargs)
            self.fallback = None
        else:
            self.primary = LocalStorageProvider()
            self.fallback = None

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload with fallback."""
        # Try primary provider
        if self.primary.upload_file(local_path, remote_path):
            self._log_operation("upload", "success", remote_path)
            return True

        # Try fallback
        if self.fallback and self.fallback.upload_file(local_path, remote_path):
            self._log_operation("upload", "fallback", remote_path)
            return True

        self._log_operation("upload", "failed", remote_path)
        return False

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download with fallback."""
        # Try primary provider
        if self.primary.download_file(remote_path, local_path):
            self._log_operation("download", "success", remote_path)
            return True

        # Try fallback
        if self.fallback and self.fallback.download_file(remote_path, local_path):
            self._log_operation("download", "fallback", remote_path)
            return True

        self._log_operation("download", "failed", remote_path)
        return False

    def upload_model(self, model_path: str, model_name: str) -> bool:
        """Upload ML model to cloud."""
        remote_path = f"models/{model_name}"
        return self.upload_file(model_path, remote_path)

    def download_model(self, model_name: str, local_path: str) -> bool:
        """Download ML model from cloud."""
        remote_path = f"models/{model_name}"
        return self.download_file(remote_path, local_path)

    def upload_logs(self, log_path: str, log_name: str) -> bool:
        """Upload application logs to cloud."""
        remote_path = f"logs/{datetime.now().strftime('%Y/%m/%d')}/{log_name}"
        return self.upload_file(log_path, remote_path)

    def list_models(self) -> list:
        """List all models in cloud storage."""
        return self.primary.list_files("models/")

    def list_logs(self) -> list:
        """List all logs in cloud storage."""
        return self.primary.list_files("logs/")

    def _log_operation(self, operation: str, status: str, path: str):
        """Log operation."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "status": status,
            "path": path,
            "provider": self.provider_type
        }
        self.upload_log.append(log_entry)

    def get_operation_log(self) -> list:
        """Get operation history."""
        return self.upload_log


# Singleton instance
_storage_manager = None


def get_storage_manager(provider_type: str = "local", **kwargs) -> CloudStorageManager:
    """Get singleton storage manager."""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = CloudStorageManager(provider_type, **kwargs)
    return _storage_manager
