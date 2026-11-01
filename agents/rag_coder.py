import chromadb
from sentence_transformers import SentenceTransformer
import os
import glob

class RAGCoder:
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection("codebase")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
    def index_codebase(self, directory):
        """Index all code files in directory"""
        print(f"Indexing {directory}...")
        
        for filepath in glob.glob(f"{directory}/**/*.py", recursive=True):
            with open(filepath, 'r') as f:
                code = f.read()
                
            # Chunk code (simple: by file for now)
            embedding = self.embedder.encode(code)
            
            self.collection.add(
                documents=[code],
                embeddings=[embedding.tolist()],
                metadatas=[{"file": filepath}],
                ids=[filepath]
            )
        
        print("Indexing complete!")
    
    def search(self, query, top_k=3):
        """Search codebase for relevant code"""
        query_embedding = self.embedder.encode(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )
        
        return results

# Test:
if __name__ == "__main__":
    rag = RAGCoder()
    
    # Index your project (or any Python project)
    rag.index_codebase(".")
    
    # Search
    results = rag.search("function to read files")
    print(results)