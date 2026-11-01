import requests
from rag_coder import RAGCoder

class ContextAwareCoder:
    def __init__(self):
        self.rag = RAGCoder()
        self.base_url = "http://localhost:11434"
        self.model = "qwen2.5-coder:7b"
    
    def generate_with_context(self, task, codebase_dir):
        """Generate code using codebase context"""
        
        # 1. Index codebase
        self.rag.index_codebase(codebase_dir)
        
        # 2. Find relevant code
        context = self.rag.search(task, top_k=3)
        
        # 3. Build enriched prompt
        prompt = f"""Task: {task}

Relevant code from this project:
{context['documents'][0]}

Generate code that follows the patterns above."""
        
        # 4. Generate
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
        )
        
        return response.json()["response"]

# Test:
if __name__ == "__main__":
    coder = ContextAwareCoder()
    
    result = coder.generate_with_context(
        task="Create a function to save data to file",
        codebase_dir="."
    )
    
    print(result)