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

## Workflow

1. **View Task**: `python main.py task <day>` - See what to build
2. **Write Code**: Create `submissions/dayXX/answer.py` with your solution
3. **Submit**: `python main.py submit <day> submissions/dayXX/answer.py`
4. **Auto Test**: System runs pytest against your code
5. **AI Code Review**: DeepSeek analyzes code quality (6 dimensions)
6. **Get Score**: Final score = 70% test + 30% AI review

## AI Code Review Flow

```
提交代码
    |
    v
pytest (功能正确性)
    |
    v
CodeReviewAgent (代码质量)
    |--- 代码正确性
    |--- 代码结构
    |--- Python规范
    |--- 性能
    |--- 潜在Bug
    |--- 知识漏洞
    |
    v
综合评分 (70% test + 30% AI)
    |
    v
生成学习建议
```

**设计原则**:
- pytest负责判断功能正确/错误
- AI负责分析代码质量和学习指导
- AI不可用时只使用测试分数
- 不直接给答案，引导学生思考

## Project Structure

```
├── main.py                    # CLI entry point
├── requirements.txt
├── configs/config.yaml
├── tasks/                     # 40-day task files
├── submissions/               # Code submissions
├── tests/                     # Test files (import from answer.py)
├── src/
│   ├── core/                  # Core platform
│   ├── evaluator/             # Code evaluation (TestEngine, CodeExecutor)
│   ├── agents/                # AI agents (DeepSeek)
│   ├── llm/                   # LLM client
│   ├── database/              # SQLite storage
│   ├── rag/                   # Knowledge base
│   └── utils/                 # Utilities
├── logs/evaluations/          # Evaluation history
└── data/                      # Data storage
```

## 40-Day Learning Path

- **Phase 1 (Day 1-7)**: Python Engineering
- **Phase 2 (Day 8-18)**: PyTorch
- **Phase 3 (Day 19-30)**: Deep Learning
- **Phase 4 (Day 31-40)**: AI Agent

## Scoring System

- **Test Score**: 70% weight
- **AI Review**: 30% weight
- **Syntax Error**: 0 points
- **Timeout**: 0 points
- **No AI**: Test score only

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific day test
python -m pytest tests/day01_test.py -v
```
