import asyncio
from typing import List, Optional
from uuid import UUID

from auth.utils import get_current_user
from common.response import APIResponse, success_response
from database.db_client import get_db
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import StreamingResponse
from models.user import User
from schemas.file import UploadedFileResponse
from services.file_service import file_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=APIResponse[UploadedFileResponse])
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    uploaded_file = await file_service.upload_file(
        db, current_user.id, file, session_id
    )

    from services.document_processor import document_processor

    asyncio.create_task(document_processor.process_file(uploaded_file.id))

    return success_response(
        UploadedFileResponse.model_validate(uploaded_file),
        message="File uploaded successfully",
    )


@router.get("", response_model=APIResponse[List[UploadedFileResponse]])
async def get_files(
    session_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    files = await file_service.get_user_files(
        db, current_user.id, session_id, limit, offset
    )
    return success_response(
        [UploadedFileResponse.model_validate(f) for f in files],
        message="Files fetched successfully",
    )


@router.get("/{file_id}", response_model=APIResponse[UploadedFileResponse])
async def get_file(
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file = await file_service.get_file(db, file_id, current_user.id)
    return success_response(
        UploadedFileResponse.model_validate(file), message="File fetched successfully"
    )


@router.delete("/{file_id}", response_model=APIResponse[dict])
async def delete_file(
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await file_service.delete_file(db, file_id, current_user.id)
    return success_response(
        {"file_id": str(file_id)}, message="File deleted successfully"
    )
