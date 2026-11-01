# AI Coding Team - Quick Start Guide

**Get started with the AI Coding Team system in minutes!**

---

## 🚀 Quick Start

### 1. Run a Task

```python
from agents.orchestrator import Orchestrator

# Initialize orchestrator
orchestrator = Orchestrator()

# Run a task with automatic validation and improvement
result = orchestrator.build_with_validation_iterative(
    task="Create a REST API endpoint with authentication",
    max_iterations=3
)

print(f"Success: {result['success']}")
print(f"Code: {result['code']}")
```

### 2. View System Status

```bash
# Verify all components are working
python3 verify_system.py
```

### 3. View Metrics

```bash
# View performance metrics
python3 learning/view_metrics.py --days 30
```

### 4. View Error Patterns

```bash
# View error patterns and learning insights
python3 learning/view_error_patterns.py --days 30
python3 learning/view_error_learning.py --days 30
```

### 5. Run Test Suite

```bash
# Generate test tasks (if not already done)
python3 tests/generate_test_tasks.py

# Run test suite
python3 tests/run_test_suite.py --limit 10  # Test with 10 tasks first

# View results
python3 tests/view_test_results.py
```

### 6. View Routing Stats

```bash
# View routing optimization statistics
python3 agents/view_routing_stats.py --days 30
```

### 7. View Feedback

```bash
# View user feedback dashboard
python3 view_feedback.py --days 30

# Submit sample feedback (for testing)
python3 view_feedback.py --sample
```

---

## 📚 Common Tasks

### Create a CRUD API

```python
from agents.orchestrator import Orchestrator

orchestrator = Orchestrator()
result = orchestrator.build_with_validation_iterative(
    task="Create a REST API for user management with CRUD operations. Use Flask, SQLAlchemy, and include validation.",
    max_iterations=3
)
```

### Implement an Algorithm

```python
result = orchestrator.build_with_validation_iterative(
    task="Implement binary search algorithm in Python with type hints and docstrings",
    max_iterations=3
)
```

### Generate Tests

```python
result = orchestrator.build_with_validation_iterative(
    task="Generate comprehensive pytest tests for the user management API",
    max_iterations=3
)
```

---

## 📊 Monitoring & Analytics

### View All Metrics

```bash
# Overall metrics dashboard
python3 learning/view_metrics.py --days 30

# Test suite results
python3 tests/view_test_results.py --days 30

# Routing statistics
python3 agents/view_routing_stats.py --days 30

# Feedback dashboard
python3 view_feedback.py --days 30

# Error patterns
python3 learning/view_error_patterns.py --days 30

# Error learning recommendations
python3 learning/view_error_learning.py --days 30
```

---

## 🛠️ System Configuration

### Model Configuration

Edit `config/models.yaml` to configure:
- Model names and parameters
- Routing thresholds
- Timeout settings

### Context Configuration

The system automatically detects task types and adjusts:
- Context building
- Prompt generation
- Token limits
- Tool selection

---

## 📖 Documentation

- `PROJECT_STATUS.md` - Comprehensive project status
- `COMPLETION_SUMMARY.md` - Implementation summary
- `SYSTEM_ARCHITECTURE.md` - System architecture details
- `NEXT_STEPS.md` - Next priorities and tasks

---

## ✅ System Verification

Run comprehensive verification:

```bash
python3 verify_system.py
```

This will verify:
- ✅ Metrics tracking system
- ✅ Error pattern learning
- ✅ Routing optimization
- ✅ Feedback collection
- ✅ Test suite framework
- ✅ Orchestrator integration
- ✅ All dashboards

---

## 🎯 Success Metrics

Track progress toward goals:

- **Code Generation Accuracy**: >90% (tracked via metrics)
- **Test Pass Rate**: >85% (tracked via test suite)
- **Error Rate**: <5% (tracked via error patterns)
- **Task Coverage**: >80% (10 task types supported)
- **Code Quality**: Production-ready (tracked via feedback)

---

## 🆘 Troubleshooting

### Component Not Initializing

```bash
# Check if database directories exist
ls -la ~/ai-coding-team/data/

# Verify system
python3 verify_system.py
```

### Import Errors

```bash
# Ensure you're in the project root
cd /home/mateo610/ai-coding-team

# Check Python path
python3 -c "import sys; print(sys.path)"
```

### Database Issues

Databases are stored in:
- `~/ai-coding-team/data/metrics/metrics.db`
- `~/ai-coding-team/data/error_patterns/error_patterns.db`
- `~/ai-coding-team/data/test_suite/test_results.db`
- `~/ai-coding-team/data/routing/routing_decisions.db`
- `~/ai-coding-team/data/feedback/feedback.db`

---

## 🎉 You're Ready!

The AI Coding Team system is production-ready with:
- ✅ Comprehensive metrics tracking
- ✅ Error pattern learning
- ✅ Automated test suite
- ✅ Routing optimization
- ✅ User feedback collection
- ✅ 26 consolidated tools
- ✅ 10 task type categories

**Start building!** 🚀

