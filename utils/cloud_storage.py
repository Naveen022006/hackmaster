"""
Cloud Storage Infrastructure
Supports AWS S3, Google Cloud Storage, Azure Blob, and local storage
For storing datasets, models, logs, and user data
"""

import os
import json
import shutil
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, BinaryIO, Union
from datetime import datetime
import hashlib
import threading


class StorageBackend(ABC):
    """Abstract base class for storage backends"""

    @abstractmethod
    def upload(self, local_path: str, remote_path: str) -> bool:
        pass

    @abstractmethod
    def download(self, remote_path: str, local_path: str) -> bool:
        pass

    @abstractmethod
    def delete(self, remote_path: str) -> bool:
        pass

    @abstractmethod
    def list_files(self, prefix: str = "") -> List[str]:
        pass

    @abstractmethod
    def exists(self, remote_path: str) -> bool:
        pass


class LocalStorage(StorageBackend):
    """Local filesystem storage backend"""

    def __init__(self, base_path: str):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        print(f"  LocalStorage initialized at: {base_path}")

    def _get_full_path(self, path: str) -> str:
        return os.path.join(self.base_path, path)

    def upload(self, local_path: str, remote_path: str) -> bool:
        """Copy file to storage"""
        try:
            full_path = self._get_full_path(remote_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            shutil.copy2(local_path, full_path)
            return True
        except Exception as e:
            print(f"LocalStorage upload error: {e}")
            return False

    def download(self, remote_path: str, local_path: str) -> bool:
        """Copy file from storage"""
        try:
            full_path = self._get_full_path(remote_path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            shutil.copy2(full_path, local_path)
            return True
        except Exception as e:
            print(f"LocalStorage download error: {e}")
            return False

    def delete(self, remote_path: str) -> bool:
        """Delete file from storage"""
        try:
            full_path = self._get_full_path(remote_path)
            if os.path.exists(full_path):
                os.remove(full_path)
            return True
        except Exception as e:
            print(f"LocalStorage delete error: {e}")
            return False

    def list_files(self, prefix: str = "") -> List[str]:
        """List files with prefix"""
        files = []
        search_path = self._get_full_path(prefix)

        if os.path.isdir(search_path):
            for root, _, filenames in os.walk(search_path):
                for filename in filenames:
                    full_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(full_path, self.base_path)
                    files.append(relative_path.replace('\\', '/'))
        elif os.path.isfile(search_path):
            files.append(prefix)

        return files

    def exists(self, remote_path: str) -> bool:
        """Check if file exists"""
        return os.path.exists(self._get_full_path(remote_path))

    def get_size(self, remote_path: str) -> int:
        """Get file size"""
        full_path = self._get_full_path(remote_path)
        if os.path.exists(full_path):
            return os.path.getsize(full_path)
        return 0

    def read_text(self, remote_path: str) -> Optional[str]:
        """Read text file"""
        try:
            with open(self._get_full_path(remote_path), 'r') as f:
                return f.read()
        except:
            return None

    def write_text(self, remote_path: str, content: str) -> bool:
        """Write text file"""
        try:
            full_path = self._get_full_path(remote_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
            return True
        except:
            return False


class AWSS3Storage(StorageBackend):
    """
    AWS S3 storage backend
    Requires: pip install boto3
    """

    def __init__(self, bucket_name: str, region: str = 'us-east-1',
                 access_key: str = None, secret_key: str = None):
        self.bucket_name = bucket_name
        self.region = region

        try:
            import boto3
            if access_key and secret_key:
                self.s3 = boto3.client(
                    's3',
                    region_name=region,
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key
                )
            else:
                # Use default credentials (environment or IAM role)
                self.s3 = boto3.client('s3', region_name=region)
            self.available = True
            print(f"  AWS S3 initialized: {bucket_name}")
        except ImportError:
            print("  WARNING: boto3 not installed. AWS S3 not available.")
            self.s3 = None
            self.available = False

    def upload(self, local_path: str, remote_path: str) -> bool:
        if not self.available:
            return False
        try:
            self.s3.upload_file(local_path, self.bucket_name, remote_path)
            return True
        except Exception as e:
            print(f"S3 upload error: {e}")
            return False

    def download(self, remote_path: str, local_path: str) -> bool:
        if not self.available:
            return False
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.s3.download_file(self.bucket_name, remote_path, local_path)
            return True
        except Exception as e:
            print(f"S3 download error: {e}")
            return False

    def delete(self, remote_path: str) -> bool:
        if not self.available:
            return False
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=remote_path)
            return True
        except Exception as e:
            print(f"S3 delete error: {e}")
            return False

    def list_files(self, prefix: str = "") -> List[str]:
        if not self.available:
            return []
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            return [obj['Key'] for obj in response.get('Contents', [])]
        except Exception as e:
            print(f"S3 list error: {e}")
            return []

    def exists(self, remote_path: str) -> bool:
        if not self.available:
            return False
        try:
            self.s3.head_object(Bucket=self.bucket_name, Key=remote_path)
            return True
        except:
            return False


class GoogleCloudStorage(StorageBackend):
    """
    Google Cloud Storage backend
    Requires: pip install google-cloud-storage
    """

    def __init__(self, bucket_name: str, credentials_path: str = None):
        self.bucket_name = bucket_name

        try:
            from google.cloud import storage
            if credentials_path:
                self.client = storage.Client.from_service_account_json(credentials_path)
            else:
                self.client = storage.Client()
            self.bucket = self.client.bucket(bucket_name)
            self.available = True
            print(f"  GCS initialized: {bucket_name}")
        except ImportError:
            print("  WARNING: google-cloud-storage not installed. GCS not available.")
            self.client = None
            self.bucket = None
            self.available = False

    def upload(self, local_path: str, remote_path: str) -> bool:
        if not self.available:
            return False
        try:
            blob = self.bucket.blob(remote_path)
            blob.upload_from_filename(local_path)
            return True
        except Exception as e:
            print(f"GCS upload error: {e}")
            return False

    def download(self, remote_path: str, local_path: str) -> bool:
        if not self.available:
            return False
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            blob = self.bucket.blob(remote_path)
            blob.download_to_filename(local_path)
            return True
        except Exception as e:
            print(f"GCS download error: {e}")
            return False

    def delete(self, remote_path: str) -> bool:
        if not self.available:
            return False
        try:
            blob = self.bucket.blob(remote_path)
            blob.delete()
            return True
        except Exception as e:
            print(f"GCS delete error: {e}")
            return False

    def list_files(self, prefix: str = "") -> List[str]:
        if not self.available:
            return []
        try:
            blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
            return [blob.name for blob in blobs]
        except Exception as e:
            print(f"GCS list error: {e}")
            return []

    def exists(self, remote_path: str) -> bool:
        if not self.available:
            return False
        try:
            blob = self.bucket.blob(remote_path)
            return blob.exists()
        except:
            return False


class CloudStorageManager:
    """
    Unified Cloud Storage Manager
    Manages multiple storage backends with sync capabilities
    """

    def __init__(self, default_backend: str = 'local'):
        self.backends: Dict[str, StorageBackend] = {}
        self.default_backend = default_backend
        self.sync_enabled = {}
        self.lock = threading.Lock()

        # Metadata tracking
        self.metadata: Dict[str, Dict] = {}

    def add_backend(self, name: str, backend: StorageBackend,
                   sync_with_default: bool = False):
        """Add storage backend"""
        self.backends[name] = backend
        self.sync_enabled[name] = sync_with_default
        print(f"  Added storage backend: {name}")

    def set_default(self, name: str):
        """Set default backend"""
        if name in self.backends:
            self.default_backend = name

    def upload(self, local_path: str, remote_path: str,
              backend: str = None, sync: bool = True) -> bool:
        """Upload file to storage"""
        backend = backend or self.default_backend
        if backend not in self.backends:
            return False

        with self.lock:
            success = self.backends[backend].upload(local_path, remote_path)

            if success:
                # Update metadata
                self.metadata[remote_path] = {
                    'backend': backend,
                    'uploaded_at': datetime.now().isoformat(),
                    'size': os.path.getsize(local_path),
                    'checksum': self._calculate_checksum(local_path)
                }

                # Sync to other backends if enabled
                if sync:
                    for name, be in self.backends.items():
                        if name != backend and self.sync_enabled.get(name):
                            be.upload(local_path, remote_path)

            return success

    def download(self, remote_path: str, local_path: str,
                backend: str = None) -> bool:
        """Download file from storage"""
        backend = backend or self.default_backend
        if backend not in self.backends:
            return False

        return self.backends[backend].download(remote_path, local_path)

    def delete(self, remote_path: str, backend: str = None,
              sync: bool = True) -> bool:
        """Delete file from storage"""
        backend = backend or self.default_backend
        if backend not in self.backends:
            return False

        with self.lock:
            success = self.backends[backend].delete(remote_path)

            if success and sync:
                # Delete from synced backends
                for name, be in self.backends.items():
                    if name != backend and self.sync_enabled.get(name):
                        be.delete(remote_path)

                # Remove metadata
                self.metadata.pop(remote_path, None)

            return success

    def list_files(self, prefix: str = "", backend: str = None) -> List[str]:
        """List files in storage"""
        backend = backend or self.default_backend
        if backend not in self.backends:
            return []

        return self.backends[backend].list_files(prefix)

    def exists(self, remote_path: str, backend: str = None) -> bool:
        """Check if file exists"""
        backend = backend or self.default_backend
        if backend not in self.backends:
            return False

        return self.backends[backend].exists(remote_path)

    def sync_backends(self, source: str, target: str, prefix: str = ""):
        """Sync files between backends"""
        if source not in self.backends or target not in self.backends:
            return

        files = self.backends[source].list_files(prefix)
        synced = 0

        for file_path in files:
            if not self.backends[target].exists(file_path):
                # Download from source, upload to target
                temp_path = f"/tmp/sync_{hashlib.md5(file_path.encode()).hexdigest()}"
                if self.backends[source].download(file_path, temp_path):
                    if self.backends[target].upload(temp_path, file_path):
                        synced += 1
                    os.remove(temp_path)

        print(f"  Synced {synced} files from {source} to {target}")

    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def get_stats(self) -> Dict:
        """Get storage statistics"""
        stats = {
            'backends': list(self.backends.keys()),
            'default_backend': self.default_backend,
            'total_files': 0,
            'by_backend': {}
        }

        for name, backend in self.backends.items():
            files = backend.list_files()
            stats['by_backend'][name] = {
                'files': len(files),
                'sync_enabled': self.sync_enabled.get(name, False)
            }
            if name == self.default_backend:
                stats['total_files'] = len(files)

        return stats


# Factory function
def create_storage_manager(config: Dict = None) -> CloudStorageManager:
    """Create storage manager with configuration"""
    config = config or {}

    manager = CloudStorageManager()

    # Always add local storage
    local_path = config.get('local_path', os.path.join(
        os.path.dirname(__file__), '..', 'storage'
    ))
    manager.add_backend('local', LocalStorage(local_path))

    # Add AWS S3 if configured
    if config.get('aws_s3'):
        s3_config = config['aws_s3']
        manager.add_backend('s3', AWSS3Storage(
            bucket_name=s3_config['bucket'],
            region=s3_config.get('region', 'us-east-1'),
            access_key=s3_config.get('access_key'),
            secret_key=s3_config.get('secret_key')
        ), sync_with_default=s3_config.get('sync', False))

    # Add GCS if configured
    if config.get('gcs'):
        gcs_config = config['gcs']
        manager.add_backend('gcs', GoogleCloudStorage(
            bucket_name=gcs_config['bucket'],
            credentials_path=gcs_config.get('credentials_path')
        ), sync_with_default=gcs_config.get('sync', False))

    return manager


# For testing
if __name__ == "__main__":
    print("=" * 60)
    print("Testing Cloud Storage Infrastructure")
    print("=" * 60)

    # Create manager with local storage only
    manager = create_storage_manager()

    print("\nStorage stats:")
    print(json.dumps(manager.get_stats(), indent=2))

    # Test local operations
    print("\nTesting local storage...")

    # Create test file
    test_content = "Hello, Cloud Storage!"
    test_file = "/tmp/test_storage.txt"
    with open(test_file, 'w') as f:
        f.write(test_content)

    # Upload
    print("  Uploading test file...")
    manager.upload(test_file, "test/test_storage.txt")

    # Check exists
    print(f"  File exists: {manager.exists('test/test_storage.txt')}")

    # List files
    print(f"  Files: {manager.list_files('test/')}")

    # Download
    download_path = "/tmp/test_download.txt"
    manager.download("test/test_storage.txt", download_path)
    with open(download_path, 'r') as f:
        print(f"  Downloaded content: {f.read()}")

    # Cleanup
    manager.delete("test/test_storage.txt")
    os.remove(test_file)
    os.remove(download_path)

    print("\nTest complete!")
