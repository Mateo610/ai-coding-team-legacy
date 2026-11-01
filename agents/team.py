from context_aware_coder import ContextAwareCoder
import requests

class Agent:
    def __init__(self, name, role, model="qwen2.5-coder:7b"):
        self.name = name
        self.role = role
        self.model = model
        self.base_url = "http://localhost:11434"
    
    def execute(self, task, context=""):
        system_prompt = f"You are a {self.role}. {context}"
        
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task}
                ],
                "stream": False
            }
        )
        
        return response.json()["message"]["content"]

class SimpleTeam:
    def __init__(self):
        self.orchestrator = Agent("Orchestrator", "project manager who breaks down tasks")
        self.coder = Agent("Coder", "software engineer who writes code")
        self.reviewer = Agent("Reviewer", "senior engineer who reviews code")
    
    def build_feature(self, request):
        print(f"🤖 Building: {request}\n")
        
        # 1. Plan
        print("📋 Planning...")
        plan = self.orchestrator.execute(
            f"Break down this task into steps: {request}"
        )
        print(f"Plan:\n{plan}\n")
        
        # 2. Code
        print("💻 Coding...")
        code = self.coder.execute(
            f"Implement: {request}\n\nPlan: {plan}"
        )
        print(f"Code:\n{code}\n")
        
        # 3. Review
        print("👀 Reviewing...")
        review = self.reviewer.execute(
            f"Review this code:\n{code}\n\nTask was: {request}"
        )
        print(f"Review:\n{review}\n")
        
        return {
            "plan": plan,
            "code": code,
            "review": review
        }

# Test:
# At the very end of team.py, add:
if __name__ == "__main__":
    print("Starting team test...")
    team = SimpleTeam()
    
    result = team.build_feature(
        "Create a REST API endpoint for user authentication"
    )
    
    print("\n=== FINAL RESULT ===")
    print(result)