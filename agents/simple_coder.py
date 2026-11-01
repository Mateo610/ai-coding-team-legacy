import requests
import json

class SimpleCoder:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.model = "qwen2.5-coder:7b"
    
    def generate_code(self, prompt):
        """Generate code from prompt"""
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
        )
        return response.json()["response"]
    
    def chat(self, messages):
        """Chat with context"""
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False
            }
        )
        return response.json()["message"]["content"]

# Test it:
if __name__ == "__main__":
    coder = SimpleCoder()
    
    result = coder.generate_code(
        "Write a Python function to check if a string is a palindrome"
    )
    
    print(result)