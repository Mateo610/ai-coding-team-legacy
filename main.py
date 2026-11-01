"""
Main CLI interface for testing
"""
import os
import sys
from agents.orchestrator import Orchestrator
from pathlib import Path
import json
from collections import defaultdict


def main():
    orchestrator = Orchestrator()

    print("\n" + "=" * 60)
    print("🤖 AI Software Team - Phase 2 (with validation)")
    print("=" * 60)

    if len(sys.argv) > 1:
        # Command line argument
        task = " ".join(sys.argv[1:])
    else:
        # Interactive mode
        print("\nWhat would you like to build?")
        print("(or 'stats' for statistics, 'quit' to exit)")
        task = input("\n> ")

    task_lower = task.lower()

    if task_lower == "quit":
        return

    if task_lower == "health":
        # Health check command
        print("\n🏥 System Health Check:")
        print("-" * 60)
        health = orchestrator.check_health()
        
        status_icon = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌",
            "unknown": "❓",
        }
        
        icon = status_icon.get(health["overall_status"], "❓")
        print(f"\n{icon} Overall Status: {health['overall_status'].upper()}")
        print(f"   Components: {health['healthy_components']}/{health['total_components']} healthy")
        print(f"   Response time: {health['response_time_ms']}ms\n")
        
        print("Component Details:")
        for component_name, component_data in health["components"].items():
            comp_icon = status_icon.get(component_data["status"], "❓")
            print(f"  {comp_icon} {component_name}: {component_data['status']}")
            if component_data.get("message"):
                print(f"     {component_data['message']}")
            if component_data.get("response_time_ms"):
                print(f"     Response: {component_data['response_time_ms']}ms")
        
        print("-" * 60)
        return

    if task_lower == "stats":
        # Don't use orchestrator.get_stats() - it only sees current session
        # Use the view_stats tool instead
        data_dir = Path.home() / "ai-coding-team" / "data" / "interactions"

        if not data_dir.exists() or not list(data_dir.glob("*.toon")):
            print("No data yet!")
            return

        total = 0
        by_route = defaultdict(int)
        scores = []

        # Read all TOON files
        for toon_file in data_dir.glob("*.toon"):
            with open(toon_file) as f:
                # Skip schema line if present; safely handle empty files
                try:
                    first_line = next(f)
                except StopIteration:
                    # Empty file, skip
                    continue

                for line in f:
                    parts = line.strip().split(", ")
                    if len(parts) >= 10:
                        total += 1
                        route = parts[6]
                        score = int(parts[7])

                        by_route[route] += 1
                        scores.append(score)

        print("\n📊 All-Time Statistics:")
        print(f"   Total interactions: {total}")
        print(f"   Local: {by_route.get('local', 0)}")
        print(f"   Claude: {by_route.get('claude', 0)}")
        if scores:
            print(f"   Avg success score: {sum(scores)/len(scores):.1f}/100")
            print(f"   Training quality (≥80): {sum(1 for s in scores if s >= 80)}")
        return

    # Use iterative validation pipeline with feedback loops
    result = orchestrator.build_with_validation_iterative(task, max_iterations=3)

    # Display generated code
    print("\n📄 Generated Code:")
    print("-" * 60)
    code = result["code"] or ""
    print(code[:1000])
    if len(code) > 1000:
        print(f"\n... ({len(code) - 1000} more characters)")
    print("-" * 60)

    # Show iteration history if available
    if "iterations" in result:
        total_iterations = result.get("total_iterations", len(result.get("iterations", [])))
        print(f"\n🔄 Iterations: {total_iterations}")
        for iter_info in result["iterations"]:
            status = "✓" if iter_info.get("success") else "✗"
            score = iter_info.get("evaluation_score", 0)
            print(f"   Iteration {iter_info['iteration']}: {status} (score: {score}/100)")
    
    # Show validation results
    val = result["validation"]
    print("\n🧪 Final Validation Results:")
    print(f"   Syntax: {'✓' if val['syntax_check']['success'] else '✗'}")
    exec_ok = val.get("execution") and val["execution"].get("success")
    print(f"   Execution: {'✓' if exec_ok else '✗'}")
    if val.get("tests_run") and val["tests_run"].get("metadata"):
        tests = val["tests_run"]["metadata"]
        total = tests.get("total", 0)
        passed = tests.get("passed", 0)
        print(f"   Tests: {passed}/{total} passed")
        if total > 0:
            print(f"   Pass rate: {(passed/total)*100:.1f}%")

    print(f"\n📈 Final quality score: {result['evaluation'].score}/100")
    print(f"💾 Logged as: {result['interaction_id']}")
    
    if result.get("success"):
        print("✅ All tests passed!")
    

if __name__ == "__main__":
    main()