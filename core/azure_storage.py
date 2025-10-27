"""
Azure Storage Service for Claude IPA MVP
Handles screenshot storage, log files, and workflow data persistence
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from io import BytesIO

from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.exceptions import AzureError

logger = logging.getLogger(__name__)

class AzureStorageService:
    """
    Azure Storage service for Claude IPA MVP.
    Handles blob storage for screenshots, logs, and workflow data.
    """
    
    def __init__(self):
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.screenshots_container = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "claude-ipa-screenshots")
        self.logs_container = os.getenv("AZURE_STORAGE_CONTAINER_LOGS", "claude-ipa-logs")
        
        self.blob_service_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Azure Blob Service Client"""
        try:
            if not self.connection_string:
                logger.warning("Azure Storage connection string not provided. Storage will be disabled.")
                return
            
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
            
            # Ensure containers exist
            self._ensure_containers_exist()
            
            logger.info("Azure Storage service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure Storage: {str(e)}")
            self.blob_service_client = None
    
    def _ensure_containers_exist(self):
        """Ensure required containers exist"""
        if not self.blob_service_client:
            return
        
        containers = [self.screenshots_container, self.logs_container]
        
        for container_name in containers:
            try:
                container_client = self.blob_service_client.get_container_client(container_name)
                if not container_client.exists():
                    container_client.create_container()
                    logger.info(f"Created Azure container: {container_name}")
                else:
                    logger.info(f"Azure container exists: {container_name}")
            except Exception as e:
                logger.error(f"Failed to create container {container_name}: {str(e)}")
    
    async def upload_screenshot(
        self, 
        screenshot_data: bytes, 
        workflow_id: str, 
        step_name: str = "screenshot"
    ) -> Optional[str]:
        """
        Upload screenshot to Azure Storage
        
        Args:
            screenshot_data: Screenshot image data
            workflow_id: Unique workflow identifier
            step_name: Name of the step (e.g., 'initial', 'final', 'step_1')
            
        Returns:
            Blob URL if successful, None if failed
        """
        if not self.blob_service_client:
            logger.warning("Azure Storage not available, saving locally")
            return await self._save_screenshot_locally(screenshot_data, workflow_id, step_name)
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            blob_name = f"screenshots/{workflow_id}/{step_name}_{timestamp}.png"
            
            blob_client = self.blob_service_client.get_blob_client(
                container=self.screenshots_container,
                blob=blob_name
            )
            
            blob_client.upload_blob(screenshot_data, overwrite=True)
            
            blob_url = blob_client.url
            logger.info(f"Screenshot uploaded: {blob_url}")
            
            return blob_url
            
        except Exception as e:
            logger.error(f"Failed to upload screenshot: {str(e)}")
            return await self._save_screenshot_locally(screenshot_data, workflow_id, step_name)
    
    async def upload_workflow_log(
        self, 
        log_data: str, 
        workflow_id: str
    ) -> Optional[str]:
        """
        Upload workflow execution log to Azure Storage
        
        Args:
            log_data: Log content as string
            workflow_id: Unique workflow identifier
            
        Returns:
            Blob URL if successful, None if failed
        """
        if not self.blob_service_client:
            logger.warning("Azure Storage not available, saving locally")
            return await self._save_log_locally(log_data, workflow_id)
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            blob_name = f"logs/{workflow_id}/execution_log_{timestamp}.json"
            
            blob_client = self.blob_service_client.get_blob_client(
                container=self.logs_container,
                blob=blob_name
            )
            
            blob_client.upload_blob(log_data.encode('utf-8'), overwrite=True)
            
            blob_url = blob_client.url
            logger.info(f"Workflow log uploaded: {blob_url}")
            
            return blob_url
            
        except Exception as e:
            logger.error(f"Failed to upload workflow log: {str(e)}")
            return await self._save_log_locally(log_data, workflow_id)
    
    async def upload_workflow_data(
        self, 
        workflow_data: Dict[str, Any], 
        workflow_id: str
    ) -> Optional[str]:
        """
        Upload workflow execution data to Azure Storage
        
        Args:
            workflow_data: Workflow execution data
            workflow_id: Unique workflow identifier
            
        Returns:
            Blob URL if successful, None if failed
        """
        if not self.blob_service_client:
            logger.warning("Azure Storage not available, saving locally")
            return await self._save_workflow_data_locally(workflow_data, workflow_id)
        
        try:
            import json
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            blob_name = f"workflows/{workflow_id}/workflow_data_{timestamp}.json"
            
            blob_client = self.blob_service_client.get_blob_client(
                container=self.logs_container,
                blob=blob_name
            )
            
            json_data = json.dumps(workflow_data, indent=2, default=str)
            blob_client.upload_blob(json_data.encode('utf-8'), overwrite=True)
            
            blob_url = blob_client.url
            logger.info(f"Workflow data uploaded: {blob_url}")
            
            return blob_url
            
        except Exception as e:
            logger.error(f"Failed to upload workflow data: {str(e)}")
            return await self._save_workflow_data_locally(workflow_data, workflow_id)
    
    async def download_screenshot(self, blob_url: str) -> Optional[bytes]:
        """
        Download screenshot from Azure Storage
        
        Args:
            blob_url: URL of the blob to download
            
        Returns:
            Screenshot data if successful, None if failed
        """
        if not self.blob_service_client:
            logger.warning("Azure Storage not available")
            return None
        
        try:
            blob_client = BlobClient.from_blob_url(blob_url)
            download_stream = blob_client.download_blob()
            return download_stream.readall()
            
        except Exception as e:
            logger.error(f"Failed to download screenshot: {str(e)}")
            return None
    
    async def list_workflow_files(self, workflow_id: str) -> List[Dict[str, Any]]:
        """
        List all files for a specific workflow
        
        Args:
            workflow_id: Unique workflow identifier
            
        Returns:
            List of file information
        """
        if not self.blob_service_client:
            return []
        
        files = []
        
        try:
            # List screenshots
            screenshots_container = self.blob_service_client.get_container_client(self.screenshots_container)
            for blob in screenshots_container.list_blobs(name_starts_with=f"screenshots/{workflow_id}/"):
                files.append({
                    "type": "screenshot",
                    "name": blob.name,
                    "url": f"{screenshots_container.url}/{blob.name}",
                    "size": blob.size,
                    "last_modified": blob.last_modified
                })
            
            # List logs
            logs_container = self.blob_service_client.get_container_client(self.logs_container)
            for blob in logs_container.list_blobs(name_starts_with=f"logs/{workflow_id}/"):
                files.append({
                    "type": "log",
                    "name": blob.name,
                    "url": f"{logs_container.url}/{blob.name}",
                    "size": blob.size,
                    "last_modified": blob.last_modified
                })
            
            # List workflow data
            for blob in logs_container.list_blobs(name_starts_with=f"workflows/{workflow_id}/"):
                files.append({
                    "type": "workflow_data",
                    "name": blob.name,
                    "url": f"{logs_container.url}/{blob.name}",
                    "size": blob.size,
                    "last_modified": blob.last_modified
                })
            
        except Exception as e:
            logger.error(f"Failed to list workflow files: {str(e)}")
        
        return files
    
    def is_available(self) -> bool:
        """Check if Azure Storage is available"""
        return self.blob_service_client is not None
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage service information"""
        return {
            "available": self.is_available(),
            "screenshots_container": self.screenshots_container,
            "logs_container": self.logs_container,
            "connection_string_configured": bool(self.connection_string)
        }
    
    # Local fallback methods
    async def _save_screenshot_locally(self, screenshot_data: bytes, workflow_id: str, step_name: str) -> str:
        """Save screenshot locally as fallback"""
        os.makedirs("screenshots", exist_ok=True)
        os.makedirs(f"screenshots/{workflow_id}", exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshots/{workflow_id}/{step_name}_{timestamp}.png"
        
        with open(filename, "wb") as f:
            f.write(screenshot_data)
        
        logger.info(f"Screenshot saved locally: {filename}")
        return filename
    
    async def _save_log_locally(self, log_data: str, workflow_id: str) -> str:
        """Save log locally as fallback"""
        os.makedirs("logs", exist_ok=True)
        os.makedirs(f"logs/{workflow_id}", exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/{workflow_id}/execution_log_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(log_data)
        
        logger.info(f"Log saved locally: {filename}")
        return filename
    
    async def _save_workflow_data_locally(self, workflow_data: Dict[str, Any], workflow_id: str) -> str:
        """Save workflow data locally as fallback"""
        os.makedirs("logs", exist_ok=True)
        os.makedirs(f"logs/{workflow_id}", exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/{workflow_id}/workflow_data_{timestamp}.json"
        
        import json
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(workflow_data, f, indent=2, default=str)
        
        logger.info(f"Workflow data saved locally: {filename}")
        return filename

# Global instance
azure_storage = AzureStorageService()
