import asyncio
import os
import traceback
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

from api.v1.chat.chunking_service import chunking_service
from common.embedding_service import embedding_service
from common.logger import get_logger
from database.db_client import AsyncSessionLocal
from models.file_chunk import FileChunk
from models.uploaded_file import ProcessingStatus, UploadedFile
from sqlalchemy import select, update

logger = get_logger(__name__)

# Thread pool executor for CPU-intensive operations
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="doc_processor")


class DocumentProcessor:
    async def process_file(self, file_id: UUID):
        """Process uploaded file: extract text, chunk, embed, and store"""
        logger.info(f"Starting to process file {file_id}")

        async with AsyncSessionLocal() as db:
            try:
                # Get file from database
                stmt = select(UploadedFile).where(UploadedFile.id == file_id)
                result = await db.execute(stmt)
                file = result.scalar_one_or_none()

                if not file:
                    logger.error(f"File {file_id} not found in database")
                    return

                logger.info(
                    f"Processing file: {file.filename} at path: {file.file_path}"
                )

                # Check if file exists
                if not os.path.exists(file.file_path):
                    logger.error(f"File path does not exist: {file.file_path}")
                    file.processing_status = ProcessingStatus.FAILED
                    await db.commit()
                    return

                # Update status to PROCESSING
                file.processing_status = ProcessingStatus.PROCESSING
                await db.commit()
                logger.info(f"File {file_id} status updated to PROCESSING")

                # Extract text from document using Docling
                # Run Docling conversion in thread pool to avoid blocking event loop
                def convert_with_docling(file_path: str) -> str:
                    """Synchronous Docling conversion function to run in thread pool.

                    Optimized for fast processing of text-based PDFs:
                    - OCR disabled by default (only needed for scanned PDFs)
                    - Table structure disabled (faster, still extracts table text)
                    - Code/formula enrichment disabled (faster processing)
                    - Docling will extract text content efficiently
                    """
                    from docling.datamodel.base_models import InputFormat
                    from docling.datamodel.pipeline_options import PdfPipelineOptions
                    from docling.document_converter import (
                        DocumentConverter,
                        PdfFormatOption,
                    )

                    # Configure pipeline options for FAST text extraction
                    # Most PDFs have extractable text, so we disable expensive operations
                    pipeline_options = PdfPipelineOptions()

                    # Disable OCR by default - only needed for scanned PDFs
                    # Docling can extract text from most PDFs without OCR
                    pipeline_options.do_ocr = False

                    # Disable table structure detection - still extracts table text, just not structured
                    # This saves significant processing time (2-3 seconds per page)
                    pipeline_options.do_table_structure = False

                    # Disable code and formula enrichment - faster processing
                    # These are only needed if you need structured code/formula extraction
                    pipeline_options.do_code_enrichment = False
                    pipeline_options.do_formula_enrichment = False

                    # Create converter with optimized options
                    converter = DocumentConverter(
                        format_options={
                            InputFormat.PDF: PdfFormatOption(
                                pipeline_options=pipeline_options
                            )
                        }
                    )

                    # Convert document - Docling handles all formats automatically
                    conv_result = converter.convert(file_path)

                    # Export to markdown - this gives clean, structured text
                    markdown_content = conv_result.document.export_to_markdown()

                    return markdown_content

                def read_as_text(file_path: str) -> str:
                    """Fallback: read file as text."""
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        return f.read()

                markdown = None
                try:
                    logger.info(
                        f"Attempting to convert file with Docling: {file.filename}"
                    )
                    # Run in thread pool with timeout
                    loop = asyncio.get_event_loop()
                    markdown = await asyncio.wait_for(
                        loop.run_in_executor(
                            _executor, convert_with_docling, file.file_path
                        ),
                        timeout=300.0,  # 5 minute timeout
                    )
                    logger.info(
                        f"Docling conversion successful. Text length: {len(markdown)}"
                    )
                except ImportError as e:
                    logger.warning(f"Docling not available ({e}), reading file as text")
                    loop = asyncio.get_event_loop()
                    markdown = await loop.run_in_executor(
                        _executor, read_as_text, file.file_path
                    )
                    logger.info(f"Read file as text. Length: {len(markdown)}")
                except asyncio.TimeoutError:
                    logger.error(
                        f"Docling conversion timed out after 5 minutes for file {file_id}"
                    )
                    file.processing_status = ProcessingStatus.FAILED
                    await db.commit()
                    return
                except Exception as e:
                    logger.error(
                        f"Docling conversion failed: {e}\n{traceback.format_exc()}"
                    )
                    logger.warning("Falling back to text reading")
                    try:
                        loop = asyncio.get_event_loop()
                        markdown = await loop.run_in_executor(
                            _executor, read_as_text, file.file_path
                        )
                        logger.info(
                            f"Fallback text reading successful. Length: {len(markdown)}"
                        )
                    except Exception as fallback_error:
                        logger.error(
                            f"Fallback text reading also failed: {fallback_error}"
                        )
                        file.processing_status = ProcessingStatus.FAILED
                        await db.commit()
                        return

                # Sanitize text: remove null bytes (PostgreSQL can't handle them)
                markdown = markdown.replace("\x00", "")
                logger.info(f"Sanitized text. Final length: {len(markdown)}")

                if not markdown or len(markdown.strip()) < 10:
                    logger.error(f"No meaningful content extracted from file {file_id}")
                    file.processing_status = ProcessingStatus.FAILED
                    await db.commit()
                    return

                # Chunk the text
                logger.info(f"Chunking text for file {file_id}")
                chunks = chunking_service.chunk_text(
                    markdown, chunk_size=1000, overlap=200
                )
                logger.info(f"Created {len(chunks)} chunks for file {file_id}")

                if not chunks:
                    logger.error(f"No chunks created for file {file_id}")
                    file.processing_status = ProcessingStatus.FAILED
                    await db.commit()
                    return

                # Generate embeddings
                logger.info(f"Generating embeddings for {len(chunks)} chunks")
                try:
                    embeddings = await embedding_service.batch_embeddings(
                        [chunk.content for chunk in chunks]
                    )
                    logger.info(f"Generated {len(embeddings)} embeddings")
                except Exception as e:
                    logger.error(
                        f"Failed to generate embeddings: {e}\n{traceback.format_exc()}"
                    )
                    file.processing_status = ProcessingStatus.FAILED
                    await db.commit()
                    return

                # Save chunks to database
                logger.info(f"Saving {len(chunks)} chunks to database")
                for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    # Sanitize chunk content (remove null bytes)
                    sanitized_content = chunk.content.replace("\x00", "")

                    file_chunk = FileChunk(
                        file_id=file_id,
                        chunk_index=idx,
                        content=sanitized_content,
                        embedding=embedding,
                        meta=chunk.metadata,
                    )
                    db.add(file_chunk)

                # Update status to COMPLETED
                file.processing_status = ProcessingStatus.COMPLETED
                await db.commit()

                logger.info(
                    f"✅ Successfully processed file {file_id} ({file.filename}) into {len(chunks)} chunks"
                )

            except Exception as e:
                logger.error(
                    f"❌ Failed to process file {file_id}: {e}\n{traceback.format_exc()}"
                )
                try:
                    # Try to update status to FAILED
                    stmt = (
                        update(UploadedFile)
                        .where(UploadedFile.id == file_id)
                        .values(processing_status=ProcessingStatus.FAILED)
                    )
                    await db.execute(stmt)
                    await db.commit()
                except Exception as update_error:
                    logger.error(f"Failed to update status to FAILED: {update_error}")


document_processor = DocumentProcessor()
