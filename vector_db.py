import chromadb
from typing import List, Dict
import requests
import tiktoken
import os
import logging
import yaml

# 加载配置文件
with open("config/config.yaml", "r") as f:
    config = yaml.safe_load(f)

logger = logging.getLogger(__name__)

class VectorDB:
    def __init__(self, host: str = "localhost", port: int = 8000, persist_directory: str = "chroma_db"):
        """Initialize the vector database with a local persistence directory."""
        print(f"Loading Chroma database from: {os.path.abspath(persist_directory)}")
        self.client = chromadb.PersistentClient(path=persist_directory)  # Use persistent client
        self.encoder = tiktoken.get_encoding("cl100k_base")  # Initialize tokenizer
        self.collection = None  # Initialize collection as None
        self.api_key = config["siliconflow"]["api_key"]  # 从配置文件中读取 API 密钥
        self.chunk_size = config["vector_db"].get("chunk_size", 200)  # 从配置文件中读取 chunk_size
        self.overlap = config["vector_db"].get("overlap", 50)  # 从配置文件中读取 overlap
        
    def create_collection(self, collection_name: str):
        """Create or get a collection in Chroma"""
        self.collection = self.client.get_or_create_collection(collection_name)
        
    def store_documents(self, collection_name: str, documents: List[Dict], ids: List[str] = None):
        """Store documents in the collection"""
        if not self.collection:
            self.create_collection(collection_name)
        
        # Prepare data for Chroma
        if ids is None:
            ids = [str(idx) for idx in range(len(documents))]
        
        embeddings = []
        metadatas = []
        documents_to_store = []
        
        for doc_id, doc in zip(ids, documents):
            try:
                embedding = self._get_embedding(doc['content'])
                embeddings.append(embedding)
                metadatas.append({"title": doc['title']})
                documents_to_store.append(doc['content'])
                logger.info(f"Storing document {doc_id}: {doc['title']}")
            except Exception as e:
                logger.error(f"Skipping document {doc_id} due to error: {str(e)}")
                continue
        
        # Store in Chroma
        if ids:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents_to_store
            )
            logger.info(f"Successfully stored {len(ids)} documents in collection '{collection_name}'.")
        else:
            logger.warning("No valid documents to store.")
        
    def _get_embedding(self, text: str, chunk_size: int = None, overlap: int = None):
        """Get embedding for a given text by splitting it into overlapping chunks and merging the embeddings."""
        if chunk_size is None:
            chunk_size = self.chunk_size
        if overlap is None:
            overlap = self.overlap
        
        tokens = self.encoder.encode(text)
        if len(tokens) == 0:
            raise Exception("Input text is empty after encoding")
        
        embeddings = []
        for i in range(0, len(tokens), chunk_size - overlap):
            chunk_tokens = tokens[i:i + chunk_size]
            chunk_text = self.encoder.decode(chunk_tokens)
            print(f"Processing chunk {i} to {i + chunk_size}: {chunk_text[:100]}...")  # Log first 100 chars of chunk
            
            response = requests.post(
                "https://api.siliconflow.cn/v1/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"input": chunk_text, "model": "BAAI/bge-large-zh-v1.5"}
            )
            
            if response.status_code != 200:
                raise Exception(f"Embedding API failed with status {response.status_code}: {response.text}")
            
            data = response.json()
            if 'data' not in data or len(data['data']) == 0:
                raise Exception("Invalid response format: missing 'data' field")
            embeddings.append(data['data'][0]['embedding'])
        
        # Merge embeddings using mean pooling
        return [sum(x) / len(x) for x in zip(*embeddings)]
        
    def search(self, query_embedding, limit: int = 3):
        """Search for similar documents in the collection"""
        if not self.collection:
            raise Exception("Collection is not initialized. Please create a collection first.")
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit
        )
        
        print(f"Search results: {results}")  # Log search results
        return results 