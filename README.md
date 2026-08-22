# AI Engineer Training Platform v2.0

A 40-day AI engineer training learning system.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# View task
python main.py task 1

# Submit code
python main.py submit 1 submissions/day01/answer.py

# View progress
python main.py progress

# Interactive mode
python main.py start
```

## Project Structure

```
├── main.py                    # CLI entry point
├── requirements.txt
├── configs/config.yaml
├── tasks/                     # 40-day task files
├── submissions/               # Code submissions
├── tests/                     # Test files
├── src/
│   ├── core/                  # Core platform
│   ├── task_manager/          # Task management
│   ├── submission_manager/    # Submission management
│   ├── evaluator/             # Code evaluation
│   ├── agents/                # AI agents
│   ├── llm/                   # LLM client
│   ├── database/              # SQLite storage
│   ├── rag/                   # Knowledge base
│   └── utils/                 # Utilities
└── data/                      # Data storage
```

## 40-Day Learning Path

- **Phase 1 (Day 1-7)**: Python Engineering
- **Phase 2 (Day 8-18)**: PyTorch
- **Phase 3 (Day 19-30)**: Deep Learning
- **Phase 4 (Day 31-40)**: AI Agent

## Testing

```bash
python -m pytest tests/ -v
```