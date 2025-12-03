# models/rag_pipeline.py
import os
from typing import List, Dict
import logging
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
            logger.info("Successfully loaded existing Chroma collection")
        except:
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
    
    def initialize_from_pdfs(self, pdf_dir: str = "./data/pdfs/", force_rebuild: bool = False):
        """
        Load PDFs, chunk, embed, and store in vector DB
        """
        logger.info(f"Starting PDF initialization (force_rebuild={force_rebuild}) from {pdf_dir}")
        
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir, exist_ok=True)
            logger.warning(f"PDF directory created: {pdf_dir}")
            return {"status": "success", "message": "No PDFs found", "count": 0}

        pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
        if not pdf_files:
            logger.info("No PDF files found in directory")
            return {"status": "success", "message": "No PDFs to process", "count": 0}

        logger.info(f"Found {len(pdf_files)} PDF files")

        all_chunks = []
        all_metadatas = []

        for pdf_file in pdf_files:
            pdf_path = os.path.join(pdf_dir, pdf_file)
            logger.info(f"Processing: {pdf_file}")
            try:
                text = self.pdf_loader.load_pdf(pdf_path)
                chunks = self.text_splitter.split_text(text)
                logger.info(f"Extracted {len(chunks)} chunks from {pdf_file}")

                for chunk in chunks:
                    all_chunks.append(chunk)
                    all_metadatas.append({"source": pdf_file, "chunk_size": len(chunk)})
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {e}")

        if not all_chunks:
            return {"status": "success", "message": "No text extracted from PDFs", "count": 0}

        embeddings = self.embedding_model.embed_batch(all_chunks)
        logger.info(f"Generated {len(embeddings)} embeddings")

        # THIS IS THE KEY: Pass force_rebuild down
        self._store_embeddings(all_chunks, embeddings, all_metadatas, force_rebuild=force_rebuild)

        final_count = self.vector_store.count() if self.vector_store_type == "chroma" else len(all_chunks)
        logger.info(f"Initialization complete. Total chunks: {final_count}")

        return {
            "status": "success",
            "message": f"Successfully loaded {len(pdf_files)} PDFs",
            "count": len(all_chunks)
        }

    def _store_embeddings(self, chunks: List[str], embeddings: List[List[float]], 
                         metadatas: List[Dict], force_rebuild: bool = False):
        """Store embeddings safely — only delete if force_rebuild=True"""
        if self.vector_store_type == "chroma":
            if force_rebuild:
                try:
                    self.chroma_client.delete_collection("academic_documents")
                    logger.info("Deleted existing collection (force rebuild)")
                except:
                    pass
                self.vector_store = self.chroma_client.create_collection("academic_documents")
            else:
                # Safely reuse existing collection
                try:
                    self.vector_store = self.chroma_client.get_collection("academic_documents")
                except:
                    self.vector_store = self.chroma_client.create_collection("academic_documents")

            ids = [f"chunk_{i}" for i in range(len(chunks))]
            self.vector_store.add(
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(chunks)} chunks → total: {self.vector_store.count()}")

    def query(self, question: str, top_k: int = 5) -> Dict:
        """Query the knowledge base"""
        logger.info(f"RAG Query: {question[:100]}...")

        if not self.is_vector_store_populated():
            return {
                "answer": "The knowledge base is empty. Please initialize the system with academic PDFs first.",
                "citations": []
            }

        query_embedding = self.embedding_model.embed_text(question)

        if self.vector_store_type == "chroma":
            results = self.vector_store.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["metadatas", "documents"]
            )
            context = [
                {
                    "text": doc,
                    "metadata": meta
                }
                for doc, meta in zip(results['documents'][0], results['metadatas'][0])
            ]
        else:  # pinecone
            results = self.vector_store.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            context = [
                {
                    "text": m['metadata'].get('text', ''),
                    "metadata": {"source": m['metadata'].get('source', 'Unknown')}
                }
                for m in results['matches']
            ]

        return self.llm_client.generate_response(question, context, top_k)