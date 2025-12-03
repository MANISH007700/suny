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
            self.vector_store = self.chroma_client.get_collection(
                name="academic_documents"
            )
            logger.info("Loaded existing Chroma collection")
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
                logger.info(f"Vector store contains {count} documents")
                return count > 0
            elif self.vector_store_type == "pinecone":
                stats = self.vector_store.describe_index_stats()
                count = stats.get('total_vector_count', 0)
                logger.info(f"Vector store contains {count} documents")
                return count > 0
        except Exception as e:
            logger.error(f"Error checking vector store: {e}")
            return False
        return False
    
    def initialize_from_pdfs(self, pdf_dir: str = "./data/pdfs/", force_rebuild: bool = False):
        """
        Load PDFs, extract text, chunk, embed, and store in vector DB
        
        Args:
            pdf_dir: Directory containing PDF files
        """
        logger.info(f"Starting PDF initialization from {pdf_dir}")
        
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
            logger.warning(f"Created empty PDF directory at {pdf_dir}")
            return {"status": "success", "message": "No PDFs to process", "count": 0}
        
        pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
        
        if not pdf_files:
            logger.warning("No PDF files found")
            return {"status": "success", "message": "No PDFs to process", "count": 0, "skipped": False}
        
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        all_chunks = []
        all_metadatas = []
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(pdf_dir, pdf_file)
            logger.info(f"Processing: {pdf_file}")
            
            try:
                # Extract text
                text = self.pdf_loader.load_pdf(pdf_path)
                logger.info(f"Extracted {len(text)} characters from {pdf_file}")
                
                # Chunk text
                chunks = self.text_splitter.split_text(text)
                logger.info(f"Created {len(chunks)} chunks from {pdf_file}")
                
                # Store chunks with metadata
                for chunk in chunks:
                    all_chunks.append(chunk)
                    all_metadatas.append({
                        "source": pdf_file,
                        "chunk_size": len(chunk)
                    })
                
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {str(e)}")
                continue
        
        if not all_chunks:
            logger.warning("No chunks extracted from PDFs")
            return {"status": "success", "message": "No content extracted", "count": 0, "skipped": False}
        
        logger.info(f"Total chunks to embed: {len(all_chunks)}")
        
        # Generate embeddings
        embeddings = self.embedding_model.embed_batch(all_chunks)
        logger.info("Generated embeddings for all chunks")
        
        # Store in vector database
        self._store_embeddings(all_chunks, embeddings, all_metadatas)
        
        logger.info(f"Successfully processed {len(pdf_files)} PDFs with {len(all_chunks)} chunks")
        
        return {
            "status": "success",
            "message": f"Processed {len(pdf_files)} PDFs",
            "count": len(all_chunks),
            "skipped": False
        }
    
    def _store_embeddings(self, chunks: List[str], embeddings: List[List[float]], 
                         metadatas: List[Dict]):
        """Store embeddings in vector database"""
        if self.vector_store_type == "chroma":
            # Clear existing data
            try:
                self.chroma_client.delete_collection("academic_documents")
                self.vector_store = self.chroma_client.create_collection(
                    name="academic_documents"
                )
            except:
                pass
            
            # Add to Chroma
            ids = [f"chunk_{i}" for i in range(len(chunks))]
            self.vector_store.add(
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            logger.info("Stored embeddings in Chroma")
        
        elif self.vector_store_type == "pinecone":
            # Prepare vectors for Pinecone
            vectors = []
            for i, (embedding, chunk, metadata) in enumerate(zip(embeddings, chunks, metadatas)):
                vectors.append({
                    "id": f"chunk_{i}",
                    "values": embedding,
                    "metadata": {**metadata, "text": chunk}
                })
            
            # Upsert to Pinecone
            self.vector_store.upsert(vectors=vectors)
            logger.info("Stored embeddings in Pinecone")
    
    def query(self, question: str, top_k: int = 5) -> Dict:
        """
        Query the RAG system
        
        Args:
            question: User's question
            top_k: Number of documents to retrieve
        
        Returns:
            Dict with answer and citations
        """
        logger.info(f"Processing query: {question}")
        
        # Generate query embedding
        query_embedding = self.embedding_model.embed_text(question)
        
        # Retrieve relevant documents
        if self.vector_store_type == "chroma":
            results = self.vector_store.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            context = []
            for i in range(len(results['documents'][0])):
                context.append({
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i]
                })
        
        elif self.vector_store_type == "pinecone":
            results = self.vector_store.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            context = []
            for match in results['matches']:
                context.append({
                    "text": match['metadata'].get('text', ''),
                    "metadata": {
                        "source": match['metadata'].get('source', 'Unknown')
                    }
                })
        
        logger.info(f"Retrieved {len(context)} relevant documents")
        
        # Generate response using LLM
        response = self.llm_client.generate_response(question, context, top_k)
        
        return response