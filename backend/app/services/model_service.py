import os
import shutil
from pathlib import Path
from fastapi import UploadFile
import boto3
from botocore.exceptions import ClientError

class ModelService:
    def __init__(self):
        self.storage_backend = os.getenv("STORAGE_BACKEND", "local")  # local or s3
        
        if self.storage_backend == "s3":
            self.s3_client = boto3.client(
                's3',
                endpoint_url=os.getenv("S3_ENDPOINT_URL", "http://localhost:9000"),
                aws_access_key_id=os.getenv("S3_ACCESS_KEY", "minioadmin"),
                aws_secret_access_key=os.getenv("S3_SECRET_KEY", "minioadmin123")
            )
            self.bucket_name = os.getenv("S3_BUCKET", "ml-models")
        else:
            self.local_storage_path = Path(os.getenv("LOCAL_STORAGE_PATH", "./storage/models"))
            self.local_storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_model_file(self, model_id: int, file: UploadFile) -> str:
        """Save model file to storage backend"""
        
        filename = f"model_{model_id}_{file.filename}"
        
        if self.storage_backend == "s3":
            try:
                # Upload to S3/MinIO
                self.s3_client.upload_fileobj(
                    file.file,
                    self.bucket_name,
                    filename
                )
                return f"s3://{self.bucket_name}/{filename}"
            except ClientError as e:
                raise Exception(f"Failed to upload to S3: {str(e)}")
        
        else:
            # Save locally
            file_path = self.local_storage_path / filename
            
            try:
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                return str(file_path)
            except Exception as e:
                raise Exception(f"Failed to save file locally: {str(e)}")
    
    def delete_model_file(self, file_path: str):
        """Delete model file from storage"""
        
        if file_path.startswith("s3://"):
            # Delete from S3
            key = file_path.replace(f"s3://{self.bucket_name}/", "")
            try:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            except ClientError:
                pass  # File might not exist
        
        else:
            # Delete local file
            try:
                os.remove(file_path)
            except OSError:
                pass  # File might not exist
    
    def get_model_file_url(self, file_path: str) -> str:
        """Get downloadable URL for model file"""
        
        if file_path.startswith("s3://"):
            key = file_path.replace(f"s3://{self.bucket_name}/", "")
            try:
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': key},
                    ExpiresIn=3600  # 1 hour
                )
                return url
            except ClientError as e:
                raise Exception(f"Failed to generate presigned URL: {str(e)}")
        
        else:
            # For local files, return file path (in production, use a file server)
            return file_path
    
    def validate_model_file(self, file: UploadFile) -> bool:
        """Validate uploaded model file"""
        
        # Check file size (max 1GB)
        max_size = 1024 * 1024 * 1024  # 1GB
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > max_size:
            raise Exception("File size exceeds 1GB limit")
        
        # Check file extension
        allowed_extensions = {'.pkl', '.joblib', '.h5', '.pt', '.pth', '.onnx', '.pb'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise Exception(f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}")
        
        return True