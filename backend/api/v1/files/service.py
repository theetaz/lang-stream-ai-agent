import os
import aiofiles
from uuid import UUID, uuid4
from typing import Optional
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.uploaded_file import UploadedFile, ProcessingStatus
from common.logger import get_logger
from common.errors import NotFoundError

logger = get_logger(__name__)

class FileService:
    def __init__(self):
        self.upload_dir = "backend/uploads"
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def upload_file(
        self,
        db: AsyncSession,
        user_id: UUID,
        file: UploadFile,
        session_id: UUID  # Now required
    ) -> UploadedFile:
        file_id = uuid4()
        user_dir = os.path.join(self.upload_dir, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        
        file_path = os.path.join(user_dir, f"{file_id}_{file.filename}")
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        db_file = UploadedFile(
            id=file_id,
            user_id=user_id,
            session_id=session_id,
            filename=file.filename,
            file_path=file_path,
            file_type=file.content_type,
            file_size=len(content),
            processing_status=ProcessingStatus.PENDING
        )
        db.add(db_file)
        await db.commit()
        await db.refresh(db_file)
        
        logger.info(f"Uploaded file {file_id}: {file.filename} for user {user_id}")
        return db_file
    
    async def get_user_files(
        self,
        db: AsyncSession,
        user_id: UUID,
        session_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[UploadedFile]:
        query = select(UploadedFile).where(UploadedFile.user_id == user_id)
        
        if session_id:
            query = query.where(UploadedFile.session_id == session_id)
        
        query = query.limit(limit).offset(offset).order_by(UploadedFile.uploaded_at.desc())
        result = await db.execute(query)
        files = result.scalars().all()
        
        logger.info(f"Fetched {len(files)} files for user {user_id}")
        return list(files)
    
    async def get_file(
        self,
        db: AsyncSession,
        file_id: UUID,
        user_id: UUID
    ) -> UploadedFile:
        query = select(UploadedFile).where(
            UploadedFile.id == file_id,
            UploadedFile.user_id == user_id
        )
        result = await db.execute(query)
        file = result.scalar_one_or_none()
        
        if not file:
            raise NotFoundError(f"File {file_id} not found")
        
        return file
    
    async def update_status(
        self,
        db: AsyncSession,
        file_id: UUID,
        status: ProcessingStatus
    ):
        query = select(UploadedFile).where(UploadedFile.id == file_id)
        result = await db.execute(query)
        file = result.scalar_one_or_none()
        
        if file:
            file.processing_status = status
            await db.commit()
            logger.info(f"Updated file {file_id} status to {status.value}")
    
    async def delete_file(
        self,
        db: AsyncSession,
        file_id: UUID,
        user_id: UUID
    ):
        file = await self.get_file(db, file_id, user_id)
        
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
        
        await db.delete(file)
        await db.commit()
        
        logger.info(f"Deleted file {file_id}")

file_service = FileService()

