# models/rag_pipeline.py
import os
from typing import List, Dict
import logging
import json
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings

from models.embedding import EmbeddingModel
from models.llm_client import LLMClient
from utils.pdf_loader import PDFLoader
from utils.text_splitter import TextSplitter

load_dotenv()
logger = logging.getLogger(__name__)



class RAGPipeline:
    def __init__(self):
        """Initialize RAG Pipeline with all components"""
        logger.info("Initializing RAG Pipeline")
        
        # Initialize components
        self.embedding_model = EmbeddingModel()
        self.llm_client = LLMClient()
        self.pdf_loader = PDFLoader()
        self.text_splitter = TextSplitter()
        
        # Initialize vector store
        self.use_pinecone = os.getenv("USE_PINECONE", "false").lower() == "true"
        self._init_vector_store()
        
        logger.info("RAG Pipeline initialized successfully")
    
    def _init_vector_store(self):
        """Initialize vector database (Pinecone or Chroma)"""
        if self.use_pinecone:
            try:
                import pinecone
                pinecone_key = os.getenv("PINECONE_API_KEY")
                pinecone_env = os.getenv("PINECONE_ENVIRONMENT")
                
                if not pinecone_key or not pinecone_env:
                    raise ValueError("Pinecone credentials not found")
                
                pinecone.init(api_key=pinecone_key, environment=pinecone_env)
                
                index_name = "academic-guidance"
                if index_name not in pinecone.list_indexes():
                    pinecone.create_index(
                        index_name,
                        dimension=self.embedding_model.get_dimension(),
                        metric="cosine"
                    )
                
                self.vector_store = pinecone.Index(index_name)
                self.vector_store_type = "pinecone"
                logger.info("Using Pinecone vector store")
                
            except Exception as e:
                logger.warning(f"Failed to initialize Pinecone: {e}. Falling back to Chroma")
                self._init_chroma()
        else:
            self._init_chroma()
    
    def _init_chroma(self):
        """Initialize Chroma local vector store"""
        persist_dir = "./vector_store"
        os.makedirs(persist_dir, exist_ok=True)
        
        self.chroma_client = chromadb.PersistentClient(path=persist_dir)
        
        try:
            self.vector_store = self.chroma_client.get_collection(name="academic_documents")
            logger.info(f"Loaded existing Chroma collection with {self.vector_store.count()} documents")
        except Exception as e:
            logger.info(f"Creating new collection (reason: {e})")
            self.vector_store = self.chroma_client.create_collection(
                name="academic_documents",
                metadata={"description": "SUNY academic documents"}
            )
            logger.info("Created new Chroma collection")
        
        self.vector_store_type = "chroma"
        logger.info("Using Chroma vector store")

    def is_vector_store_populated(self) -> bool:
        """Check if vector store already has documents"""
        try:
            if self.vector_store_type == "chroma":
                count = self.vector_store.count()
                logger.info(f"Chroma vector store has {count} chunks")
                return count > 0
            elif self.vector_store_type == "pinecone":
                stats = self.vector_store.describe_index_stats()
                count = stats.get('total_vector_count', 0)
                logger.info(f"Pinecone vector store has {count} vectors")
                return count > 0
        except Exception as e:
            logger.error(f"Error checking vector store population: {e}")
            return False
        return False
    
    def get_vector_store_count(self) -> int:
        """Get the current number of documents in vector store"""
        try:
            if self.vector_store_type == "chroma":
                return self.vector_store.count()
            elif self.vector_store_type == "pinecone":
                stats = self.vector_store.describe_index_stats()
                return stats.get('total_vector_count', 0)
        except Exception as e:
            logger.error(f"Error getting vector store count: {e}")
            return 0
    
    def initialize_from_pdfs(self, pdf_dir: str = "/Users/admin/Desktop/code/work/suny/backend/data/pdfs", force_rebuild: bool = False):
        """
        Load PDFs, extract text, chunk, embed, and store in vector DB.
        
        Args:
            pdf_dir: Directory containing PDF files
            force_rebuild: If True, delete existing collection and rebuild from scratch
        
        Returns:
            Dict with status, message, and count
        """
        logger.info(f"Starting PDF initialization from {pdf_dir} (force_rebuild={force_rebuild})")
        

        abs_path = os.path.abspath(pdf_dir)
        logger.info(f"Checking PDF directory: {pdf_dir}")
        logger.info(f"Absolute path: {abs_path}")
        logger.info(f"Directory exists: {os.path.exists(pdf_dir)}")
        if os.path.exists(pdf_dir):
            files = os.listdir(pdf_dir)
            logger.info(f"Files in directory: {files}")


        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir, exist_ok=True)
            logger.warning(f"Created PDF directory: {pdf_dir}")
            return {"status": "success", "message": "No PDFs found", "count": 0}

        pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
        if not pdf_files:
            logger.info("No PDF files found")
            return {"status": "success", "message": "No PDFs to process", "count": 0}

        logger.info(f"Found {len(pdf_files)} PDF files")

        # Handle force rebuild - clear everything
        if force_rebuild:
            logger.info("Force rebuild requested - clearing vector store")
            try:
                self.chroma_client.delete_collection("academic_documents")
                logger.info("Deleted existing collection")
            except Exception as e:
                logger.info(f"No existing collection to delete: {e}")
            
            self.vector_store = self.chroma_client.create_collection(
                name="academic_documents",
                metadata={"description": "SUNY academic documents"}
            )
            logger.info("Created fresh collection")
            
            # Clear processed tracker
            processed_file = "./vector_store/processed_pdfs.json"
            if os.path.exists(processed_file):
                os.remove(processed_file)
                logger.info("Cleared processed PDFs tracker")
            
            processed_pdfs = set()
        else:
            # Load existing processed PDFs tracker
            processed_file = "./vector_store/processed_pdfs.json"
            if os.path.exists(processed_file):
                with open(processed_file, 'r') as f:
                    processed_pdfs = set(json.load(f))
                logger.info(f"Found {len(processed_pdfs)} previously processed PDFs")
            else:
                processed_pdfs = set()

        # Determine which PDFs to process
        if force_rebuild:
            pdfs_to_process = pdf_files
            logger.info(f"Force rebuild: processing all {len(pdfs_to_process)} PDFs")
        else:
            pdfs_to_process = [f for f in pdf_files if f not in processed_pdfs]
            logger.info(f"Found {len(pdfs_to_process)} new PDFs to process")
            
            if not pdfs_to_process:
                current_count = self.get_vector_store_count()
                logger.info("No new PDFs to process")
                return {
                    "status": "success", 
                    "message": "No new PDFs to process", 
                    "count": current_count,
                    "skipped": True
                }

        # Process PDFs
        all_chunks = []
        all_metadatas = []
        all_ids = []

        for pdf_file in pdfs_to_process:
            pdf_path = os.path.join(pdf_dir, pdf_file)
            logger.info(f"Processing: {pdf_file}")
            
            try:
                # Load and chunk PDF
                text = self.pdf_loader.load_pdf(pdf_path)
                chunks = self.text_splitter.split_text(text)
                logger.info(f"  -> Extracted {len(chunks)} chunks from {pdf_file}")

                # Create unique IDs and metadata for each chunk
                for idx, chunk in enumerate(chunks):
                    chunk_id = f"{pdf_file}_chunk_{idx}"
                    all_ids.append(chunk_id)
                    all_chunks.append(chunk)
                    all_metadatas.append({
                        "source": pdf_file,
                        "chunk_id": chunk_id,
                        "chunk_index": idx,
                        "chunk_size": len(chunk)
                    })
                
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {str(e)}")
                continue

        if not all_chunks:
            logger.warning("No chunks extracted from any PDF")
            return {"status": "error", "message": "No content extracted from PDFs", "count": 0}

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
        embeddings = self.embedding_model.embed_batch(all_chunks)
        logger.info(f"Generated {len(embeddings)} embeddings")

        # Store in vector database
        try:
            self.vector_store.add(
                embeddings=embeddings,
                documents=all_chunks,
                metadatas=all_metadatas,
                ids=all_ids
            )
            logger.info(f"Successfully stored {len(all_chunks)} chunks in vector store")
        except Exception as e:
            logger.error(f"Error storing embeddings: {e}")
            return {"status": "error", "message": f"Failed to store embeddings: {str(e)}", "count": 0}

        # Update processed PDFs tracker
        processed_pdfs.update(pdfs_to_process)
        os.makedirs(os.path.dirname(processed_file), exist_ok=True)
        with open(processed_file, 'w') as f:
            json.dump(list(processed_pdfs), f)
        logger.info(f"Updated tracker: {len(processed_pdfs)} total processed PDFs")

        # Get final count
        final_count = self.get_vector_store_count()
        logger.info(f"Vector store now contains {final_count} total chunks")

        return {
            "status": "success",
            "message": f"Processed {len(pdfs_to_process)} PDF(s), added {len(all_chunks)} chunks",
            "count": final_count,
            "new_chunks": len(all_chunks)
        }

    def query(self, question: str, top_k: int = 5) -> Dict:
        """Query the knowledge base"""
        logger.info(f"RAG Query: '{question[:100]}...'")

        # Check if vector store has documents
        if not self.is_vector_store_populated():
            logger.warning("Vector store is empty")
            return {
                "answer": "The knowledge base is empty. Please initialize the system with academic PDFs first.",
                "citations": []
            }

        # Generate query embedding
        query_embedding = self.embedding_model.embed_text(question)
        logger.info(f"Generated query embedding (dim: {len(query_embedding)})")

        # Retrieve relevant documents
        if self.vector_store_type == "chroma":
            try:
                results = self.vector_store.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    include=["metadatas", "documents", "distances"]
                )
                
                logger.info(f"Retrieved {len(results['documents'][0])} documents")
                logger.info(f"Distances: {results.get('distances', [[]])[0]}")
                
                # Build context from results
                context = []
                for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                    context.append({
                        "text": doc,
                        "metadata": meta
                    })
                    logger.info(f"  -> Source: {meta.get('source', 'Unknown')}, chunk: {meta.get('chunk_index', '?')}")
                
            except Exception as e:
                logger.error(f"Error querying Chroma: {e}")
                return {
                    "answer": f"Error retrieving documents: {str(e)}",
                    "citations": []
                }
        
        else:  # Pinecone
            try:
                results = self.vector_store.query(
                    vector=query_embedding,
                    top_k=top_k,
                    include_metadata=True
                )
                
                context = []
                for match in results['matches']:
                    context.append({
                        "text": match['metadata'].get('text', ''),
                        "metadata": {"source": match['metadata'].get('source', 'Unknown')}
                    })
                    
            except Exception as e:
                logger.error(f"Error querying Pinecone: {e}")
                return {
                    "answer": f"Error retrieving documents: {str(e)}",
                    "citations": []
                }

        # Generate response using LLM
        logger.info("Generating LLM response...")
        return self.llm_client.generate_response(question, context, top_k)