import os
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma

from dotenv import load_dotenv

load_dotenv()

class WomenSafetyKnowledgeBase:
    def __init__(self, data_path="data/"):
        self.data_path = data_path
        self.chroma_db_path = "./chroma_db"
        self.embedding_model = None
        self.vectorstore = None
        
    def load_pdf_files(self):
        """Load raw PDF files from data directory"""
        loader = DirectoryLoader(
            self.data_path,
            glob='*.pdf',
            loader_cls=PyPDFLoader
        )
        documents = loader.load()
        print(f"Loaded {len(documents)} PDF pages")
        return documents
    
    def create_chunks(self, extracted_data):
        """Create text chunks from documents"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        text_chunks = text_splitter.split_documents(extracted_data)
        print(f"Created {len(text_chunks)} text chunks")
        return text_chunks
    
    def get_embedding_model(self):
        """Get HuggingFace embedding model"""
        if not self.embedding_model:
            self.embedding_model = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        return self.embedding_model
    
    def create_vectorstore(self):
        """Create and save ChromaDB vectorstore"""
        print("Loading PDF documents...")
        documents = self.load_pdf_files()
        
        if not documents:
            print("No PDF documents found!")
            return None
        
        print("Creating text chunks...")
        text_chunks = self.create_chunks(documents)
        
        print("Getting embedding model...")
        embedding_model = self.get_embedding_model()
        
        print("Creating ChromaDB vectorstore...")
        self.vectorstore = Chroma.from_documents(
            documents=text_chunks,
            embedding=embedding_model,
            persist_directory=self.chroma_db_path
        )
        
        print(f"Vectorstore saved to {self.chroma_db_path}")
        print("Knowledge base created successfully!")
        return self.vectorstore
    
    def load_existing_vectorstore(self):
        """Load existing ChromaDB vectorstore"""
        if os.path.exists(self.chroma_db_path):
            print("Loading existing ChromaDB vectorstore...")
            embedding_model = self.get_embedding_model()
            self.vectorstore = Chroma(
                persist_directory=self.chroma_db_path,
                embedding_function=embedding_model
            )
            return self.vectorstore
        return None

# Initialize knowledge base
knowledge_base = WomenSafetyKnowledgeBase()

def setup_knowledge_base():
    """Setup or load knowledge base"""
    # Try to load existing vectorstore first
    if knowledge_base.load_existing_vectorstore():
        print("ChromaDB knowledge base loaded successfully!")
        return knowledge_base
    else:
        print("Creating new ChromaDB knowledge base...")
        knowledge_base.create_vectorstore()
        return knowledge_base

# Test function for database creation
if __name__ == "__main__":
    print("Creating ChromaDB Knowledge Base...")
    kb = setup_knowledge_base()
    print("Database setup complete!")
