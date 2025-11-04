from uuid import UUID
from database.db_client import AsyncSessionLocal
from api.v1.files.service import file_service
from api.v1.chat.chunking_service import chunking_service
from common.embedding_service import embedding_service
from models.uploaded_file import ProcessingStatus
from models.file_chunk import FileChunk
from common.logger import get_logger
import traceback

logger = get_logger(__name__)

class DocumentProcessor:
    async def process_file(self, file_id: UUID):
        async with AsyncSessionLocal() as db:
            try:
                file = await file_service.get_file(db, file_id, None)
                if not file:
                    logger.error(f"File {file_id} not found")
                    return
                
                await file_service.update_status(db, file_id, ProcessingStatus.PROCESSING)
                
                try:
                    from docling.document_converter import DocumentConverter
                    converter = DocumentConverter()
                    result = converter.convert(file.file_path)
                    markdown = result.document.export_to_markdown()
                except ImportError:
                    logger.warning("Docling not available, reading file as text")
                    with open(file.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        markdown = f.read()
                
                chunks = chunking_service.chunk_text(markdown, chunk_size=1000, overlap=200)
                
                embeddings = await embedding_service.batch_embeddings(
                    [chunk.content for chunk in chunks]
                )
                
                for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    file_chunk = FileChunk(
                        file_id=file_id,
                        chunk_index=idx,
                        content=chunk.content,
                        embedding=embedding,
                        meta=chunk.metadata
                    )
                    db.add(file_chunk)
                
                await db.commit()
                await file_service.update_status(db, file_id, ProcessingStatus.COMPLETED)
                
                logger.info(f"Successfully processed file {file_id} into {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"Failed to process file {file_id}: {e}\n{traceback.format_exc()}")
                await file_service.update_status(db, file_id, ProcessingStatus.FAILED)

document_processor = DocumentProcessor()

