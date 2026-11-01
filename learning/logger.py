"""
TOON-format interaction logger
Zero-overhead data collection for fine-tuning
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import hashlib


class InteractionLogger:
    """Logs all interactions in TOON format for training"""

    # TOON schema - class-level constant
    schema = [
        "timestamp",
        "interaction_id",
        "agent",
        "task_hash",
        "complexity_pred",
        "complexity_actual",
        "route",
        "success_score",
        "tokens_used",
        "duration_ms",
    ]

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(
            data_dir or os.path.expanduser("~/ai-coding-team/data/interactions")
        )
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Use daily file instead of per-session
        date_str = datetime.now().strftime("%Y%m%d")
        self.toon_file = self.data_dir / f"{date_str}.toon"
        self.metadata_file = self.data_dir / f"{date_str}_meta.jsonl"

        # Simple session identifier for interaction ids
        self.session_id = date_str

        # Initialize TOON file with schema if it doesn't exist
        if not self.toon_file.exists():
            with open(self.toon_file, "w") as f:
                f.write("@schema: " + ", ".join(self.schema) + "\n")
    
    def log_interaction(self, 
                       agent: str,
                       task: str,
                       context: str,
                       output: str,
                       complexity_pred: int,
                       complexity_actual: int = None,
                       route: str = "local",
                       success_score: int = None,
                       tokens_used: int = 0,
                       duration_ms: int = 0,
                       metadata: Dict[str, Any] = None) -> str:
        """
        Log interaction in TOON format + detailed metadata
        
        Returns interaction_id for reference
        """
        
        interaction_id = hashlib.md5(
            f"{self.session_id}_{task}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        task_hash = hashlib.md5(task.encode()).hexdigest()[:8]
        
        # TOON record (compact)
        toon_record = [
            datetime.now().isoformat(),
            interaction_id,
            agent,
            task_hash,
            complexity_pred,
            complexity_actual or complexity_pred,
            route,
            success_score or 0,
            tokens_used,
            duration_ms
        ]
        
        # Write TOON
        with open(self.toon_file, 'a') as f:
            f.write(", ".join(str(v) for v in toon_record) + "\n")
        
        # Detailed metadata (for training)
        full_metadata = {
            "interaction_id": interaction_id,
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "task": task,
            "context": context,
            "output": output,
            "complexity": {
                "predicted": complexity_pred,
                "actual": complexity_actual or complexity_pred
            },
            "route": route,
            "success_score": success_score,
            "tokens_used": tokens_used,
            "duration_ms": duration_ms,
            "metadata": metadata or {}
        }
        
        # Write metadata (ensure JSON serializable)
        with open(self.metadata_file, "a") as f:
            f.write(json.dumps(full_metadata, default=str) + "\n")
        
        return interaction_id
    
    def get_training_examples(self, min_score: int = 80) -> list:
        """
        Load high-quality interactions for fine-tuning
        """
        examples = []
        
        # Read all metadata files
        for meta_file in self.data_dir.glob("*_meta.jsonl"):
            with open(meta_file) as f:
                for line in f:
                    interaction = json.loads(line)
                    if interaction.get('success_score', 0) >= min_score:
                        examples.append({
                            "instruction": interaction['task'],
                            "input": interaction['context'],
                            "output": interaction['output'],
                            "metadata": interaction['metadata']
                        })
        
        return examples
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        total = 0
        by_route = {"local": 0, "claude": 0}
        avg_score = []
        
        with open(self.toon_file) as f:
            next(f)  # Skip schema
            for line in f:
                total += 1
                parts = line.strip().split(", ")
                route = parts[6]
                score = int(parts[7])
                
                by_route[route] = by_route.get(route, 0) + 1
                avg_score.append(score)
        
        return {
            "total_interactions": total,
            "by_route": by_route,
            "avg_success_score": sum(avg_score) / len(avg_score) if avg_score else 0
        }