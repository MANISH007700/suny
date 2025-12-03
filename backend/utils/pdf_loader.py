import os
import logging
from typing import Optional
import pypdf
import pdfplumber

logger = logging.getLogger(__name__)

class PDFLoader:
    def __init__(self, save_dir: str = "./data/processed_text/"):
        """
        Initialize PDF Loader
        
        Args:
            save_dir: Directory to save extracted text
        """
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
    
    def load_pdf(self, pdf_path: str, use_pdfplumber: bool = False) -> str:
        """
        Load and extract text from PDF
        
        Args:
            pdf_path: Path to PDF file
            use_pdfplumber: If True, use pdfplumber instead of pypdf
        
        Returns:
            Extracted text as string
        """
        logger.info(f"Loading PDF: {pdf_path}")
        
        try:
            if use_pdfplumber:
                text = self._extract_with_pdfplumber(pdf_path)
            else:
                text = self._extract_with_pypdf(pdf_path)
            
            # Save extracted text
            self._save_extracted_text(pdf_path, text)
            
            logger.info(f"Successfully extracted {len(text)} characters")
            return text
            
        except Exception as e:
            logger.error(f"Error loading PDF {pdf_path}: {str(e)}")
            raise
    
    def _extract_with_pypdf(self, pdf_path: str) -> str:
        """Extract text using pypdf"""
        text_parts = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            logger.info(f"PDF has {num_pages} pages")
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        
        return "\n\n".join(text_parts)
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> str:
        """Extract text using pdfplumber (better for tables)"""
        text_parts = []
        
        with pdfplumber.open(pdf_path) as pdf:
            num_pages = len(pdf.pages)
            logger.info(f"PDF has {num_pages} pages")
            
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        
        return "\n\n".join(text_parts)
    
    def _save_extracted_text(self, pdf_path: str, text: str):
        """Save extracted text to file"""
        filename = os.path.basename(pdf_path).replace('.pdf', '.txt')
        output_path = os.path.join(self.save_dir, filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            logger.info(f"Saved extracted text to {output_path}")
        except Exception as e:
            logger.warning(f"Could not save extracted text: {str(e)}")
    
    def batch_load_pdfs(self, pdf_dir: str) -> dict:
        """
        Load all PDFs from a directory
        
        Args:
            pdf_dir: Directory containing PDFs
        
        Returns:
            Dict mapping filename to extracted text
        """
        if not os.path.exists(pdf_dir):
            raise ValueError(f"Directory not found: {pdf_dir}")
        
        pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
        logger.info(f"Found {len(pdf_files)} PDF files in {pdf_dir}")
        
        extracted_texts = {}
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(pdf_dir, pdf_file)
            try:
                text = self.load_pdf(pdf_path)
                extracted_texts[pdf_file] = text
            except Exception as e:
                logger.error(f"Failed to load {pdf_file}: {str(e)}")
                continue
        
        logger.info(f"Successfully loaded {len(extracted_texts)} PDFs")
        return extracted_texts