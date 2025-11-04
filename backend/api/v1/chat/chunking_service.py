import tiktoken
from typing import List
from common.logger import get_logger

logger = get_logger(__name__)

class Chunk:
    def __init__(self, content: str, metadata: dict = None):
        self.content = content
        self.metadata = metadata or {}

class ChunkingService:
    def __init__(self):
        self.encoder = tiktoken.get_encoding("cl100k_base")
    
    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[Chunk]:
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_tokens = self.encoder.encode(para)
            para_size = len(para_tokens)
            
            if current_size + para_size <= chunk_size:
                current_chunk.append(para)
                current_size += para_size
            else:
                if current_chunk:
                    chunk_text = '\n\n'.join(current_chunk)
                    chunks.append(Chunk(
                        content=chunk_text,
                        metadata={"tokens": current_size}
                    ))
                
                current_chunk = [para]
                current_size = para_size
        
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(Chunk(
                content=chunk_text,
                metadata={"tokens": current_size}
            ))
        
        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks

chunking_service = ChunkingService()

