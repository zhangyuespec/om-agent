from wiki_fetcher import WikiDataFetcher
from vector_db import VectorDB
import requests
import logging
import os
import json
import yaml
from dotenv import load_dotenv

# 加载配置文件
with open("config/config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpsAgent:
    def __init__(self, wiki_domain: str, wiki_username: str, wiki_password: str, persist_directory: str = "chroma_db"):
        """Initialize the agent with a local Chroma database."""
        self.wiki_fetcher = WikiDataFetcher(wiki_domain, wiki_username, wiki_password)
        self.vector_db = VectorDB(persist_directory=persist_directory)  # Load local Chroma database
        self.initialized = self._check_database_initialized()  # Check if database is already initialized
        self.api_key = config["siliconflow"]["api_key"]  # 从配置文件中读取 API 密钥
        
    def _check_database_initialized(self):
        """Check if the Chroma database is already initialized."""
        try:
            # Attempt to load the default collection
            self.vector_db.create_collection("ops_docs")
            collection_info = self.vector_db.collection.get()
            if len(collection_info['ids']) > 0:
                logger.info(f"Chroma database is already initialized with {len(collection_info['ids'])} documents.")
                return True
            else:
                logger.warning("Chroma database exists but is empty.")
                return False
        except Exception as e:
            logger.error(f"Error checking database initialization: {str(e)}")
            return False
        
    def initialize(self, page_id: str):
        """Initialize the agent by fetching and storing wiki data"""
        documents = self.wiki_fetcher.fetch_page_and_children(page_id)
        if not documents:
            logger.error("No documents fetched from the wiki.")
            return
        
        # 检查集合是否已存在
        if not self.initialized:
            self.vector_db.create_collection("ops_docs")
            logger.info("Created new collection 'ops_docs'")
        else:
            logger.info("Using existing collection 'ops_docs'")
        
        # 获取现有文档的 ID
        existing_ids = set(self.vector_db.collection.get()['ids'])
        
        # 存储新文档
        new_documents = []
        for idx, doc in enumerate(documents):
            # 生成唯一 ID
            doc_id = f"{page_id}_{idx}"
            if doc_id not in existing_ids:
                new_documents.append((doc_id, doc))
        
        if new_documents:
            self.vector_db.store_documents("ops_docs", [doc for _, doc in new_documents], [doc_id for doc_id, _ in new_documents])
            logger.info(f"Added {len(new_documents)} new documents to the collection.")
        else:
            logger.info("No new documents to add.")
        
        self.initialized = True
        
    def query(self, question: str) -> str:
        """Query the agent with a question"""
        if not self.initialized:
            return "Vector database is not initialized. Please initialize first."
            
        # First, find relevant documents
        query_embedding = self.vector_db._get_embedding(question)
        search_result = self.vector_db.search(query_embedding, limit=3)
        
        # Build context from relevant documents
        context = "\n".join(search_result['documents'][0])
        
        # Query SiliconFlow's chat API directly
        response = requests.post(
            "https://api.siliconflow.cn/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": "deepseek-ai/DeepSeek-V2.5",
                "messages": [
                    {"role": "system", "content": "You are an operations and maintenance assistant. Use the following context to answer questions:"},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
        )
        
        return response.json()['choices'][0]['message']['content']

    def stream_query(self, question: str):
        """Stream the response for a question"""
        if not self.initialized:
            logger.error("Vector database is not initialized.")
            yield "data: " + json.dumps({"error": "Vector database is not initialized. Please initialize first."}) + "\n\n"
            return
        
        try:
            # First, find relevant documents
            query_embedding = self.vector_db._get_embedding(question)
            search_result = self.vector_db.search(query_embedding, limit=3)
            
            # Build context from relevant documents
            context = "\n".join(search_result['documents'][0])
            logger.info(f"Context for question: {context[:100]}...")  # Log first 100 chars of context
            
            # Stream the response
            response = requests.post(
                "https://api.siliconflow.cn/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "deepseek-ai/DeepSeek-V2.5",
                    "messages": [
                        {"role": "system", "content": "You are an operations and maintenance assistant. Use the following context to answer questions:"},
                        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "stream": True  # Enable streaming
                },
                stream=True
            )
            
            if response.status_code != 200:
                logger.error(f"API request failed with status {response.status_code}: {response.text}")
                yield "data: " + json.dumps({"error": f"API request failed with status {response.status_code}"}) + "\n\n"
                return
            
            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    decoded_chunk = chunk.decode('utf-8')
                    if decoded_chunk.startswith("data: "):
                        yield decoded_chunk + "\n"
                    else:
                        yield "data: " + json.dumps({"answer": decoded_chunk}) + "\n\n"
            
            # Send the [DONE] marker at the end
            yield "data: " + json.dumps({"done": True}) + "\n\n"
        except Exception as e:
            logger.error(f"Error in stream_query: {str(e)}")
            yield "data: " + json.dumps({"error": str(e)}) + "\n\n"

# Initialize with a specific page
# agent.initialize("76418066")

# Initialize OpsAgent
agent = OpsAgent(
    wiki_domain=config["wiki"]["domain"],
    wiki_username=config["wiki"]["username"],
    wiki_password=config["wiki"]["password"],
    persist_directory=config["vector_db"]["persist_directory"]
)

# Query the agent
response = agent.query("How do I restart the production server?")
print(response) 