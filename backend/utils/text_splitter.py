import logging
from typing import List

logger = logging.getLogger(__name__)

class TextSplitter:
    def __init__(self, chunk_size: int = 1200, chunk_overlap: int = 100):
        """
        Initialize text splitter
        
        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Overlap between consecutive chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logger.info(f"TextSplitter initialized: chunk_size={chunk_size}, overlap={chunk_overlap}")
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Input text to split
        
        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to split_text")
            return []
        
        # Clean the text
        text = self._clean_text(text)
        
        # Split into chunks
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # Calculate end position
            end = start + self.chunk_size
            
            # If not at the end, try to break at sentence boundary
            if end < text_length:
                # Look for sentence endings
                sentence_end = self._find_sentence_boundary(text, start, end)
                if sentence_end != -1:
                    end = sentence_end
            else:
                # At the end, just take what's left
                end = text_length
            
            # Extract chunk
            chunk = text[start:end].strip()
            
            if chunk:
                chunks.append(chunk)
            
            # Move to next chunk with overlap
            next_start = end - self.chunk_overlap
            
            # Ensure we make progress (prevent infinite loop)
            if next_start <= start:
                next_start = end
            
            start = next_start
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove page numbers and common artifacts
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip very short lines (likely page numbers or headers)
            if len(line) > 3:
                cleaned_lines.append(line)
        
        return ' '.join(cleaned_lines)
    
    def _find_sentence_boundary(self, text: str, start: int, end: int) -> int:
        """
        Find the best sentence boundary near the end position
        
        Args:
            text: Full text
            start: Start position of chunk
            end: Desired end position
        
        Returns:
            Position of sentence boundary, or -1 if not found
        """
        # Look for sentence endings within a window
        search_window = 100
        search_start = max(start, end - search_window)
        search_text = text[search_start:end]
        
        # Find last occurrence of sentence endings
        sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
        
        best_pos = -1
        for ending in sentence_endings:
            pos = search_text.rfind(ending)
            if pos != -1:
                actual_pos = search_start + pos + len(ending)
                if actual_pos > best_pos:
                    best_pos = actual_pos
        
        return best_pos if best_pos > start else -1
    
    def split_by_paragraphs(self, text: str) -> List[str]:
        """
        Split text by paragraphs (for documents with clear paragraph structure)
        
        Args:
            text: Input text
        
        Returns:
            List of paragraph chunks
        """
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If adding this paragraph exceeds chunk_size, save current chunk
            if len(current_chunk) + len(para) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        logger.info(f"Split text into {len(chunks)} paragraph-based chunks")
        return chunks