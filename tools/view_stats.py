"""View training data and statistics"""

import json
from pathlib import Path
from collections import defaultdict

def view_all_stats():
    data_dir = Path.home() / "ai-coding-team" / "data" / "interactions"
    
    if not data_dir.exists():
        print("No data yet!")
        return
    
    total = 0
    by_route = defaultdict(int)
    by_agent = defaultdict(int)
    scores = []
    
    # Read all TOON files
    for toon_file in data_dir.glob("*.toon"):
        with open(toon_file) as f:
            schema_line = f.readline()  # Skip schema
            
            for line in f:
                parts = line.strip().split(", ")
                if len(parts) >= 10:
                    total += 1
                    route = parts[6]
                    agent = parts[2]
                    score = int(parts[7])
                    
                    by_route[route] += 1
                    by_agent[agent] += 1
                    scores.append(score)
    
    print("\n" + "="*60)
    print("📊 ALL-TIME STATISTICS")
    print("="*60)
    print(f"\nTotal interactions: {total}")
    
    if total > 0:
        print(f"\nBy route:")
        for route, count in by_route.items():
            print(f"  {route}: {count} ({count/total*100:.1f}%)")
        
        print(f"\nBy agent:")
        for agent, count in by_agent.items():
            print(f"  {agent}: {count}")
        
        print(f"\nScores:")
        print(f"  Average: {sum(scores)/len(scores):.1f}/100")
        print(f"  Min: {min(scores)}")
        print(f"  Max: {max(scores)}")
        print(f"  >= 80 (training quality): {sum(1 for s in scores if s >= 80)} ({sum(1 for s in scores if s >= 80)/len(scores)*100:.1f}%)")
    
    # Show training examples available
    training_examples = []
    for meta_file in data_dir.glob("*_meta.jsonl"):
        with open(meta_file) as f:
            for line in f:
                interaction = json.loads(line)
                if interaction.get('success_score', 0) >= 80:
                    training_examples.append(interaction)
    
    print(f"\n🎓 Training examples available: {len(training_examples)}")
    print("="*60)

if __name__ == "__main__":
    view_all_stats()