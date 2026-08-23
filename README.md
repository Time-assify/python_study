# AI Engineer Training Platform v2.0

A 40-day AI engineer training learning system.

## Quick Start

```bash
# Day01-Day07: 基础依赖
pip install -r requirements.txt

# 进入Day08(PyTorch)前:
pip install -r requirements-pytorch.txt

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
6. **Get Score**: pytest是功能正确性的核心依据；测试达到60分且AI可用时采用 70% Test + 30% AI；AI不可用或test_score<60时使用test_score；syntax/execution/timeout失败为0。详见下方 Scoring Rules

## AI Code Review Flow

```
提交代码
    |
    v
pytest (功能正确性 - 唯一判分依据)
    |
    v
CodeReviewAgent (代码质量, 不判断功能对错)
    |--- 代码结构
    |--- Python/PyTorch规范
    |--- 可读性
    |--- 性能
    |--- 潜在工程问题
    |--- 知识漏洞 (结合历史错误)
    |
    v
综合评分
    |
    v
保存 LearningRecord
    |
    v
更新 StudentProfile
    |
    v
生成下一步学习建议
```

**设计原则**:
- pytest负责判断功能正确/错误
- AI只负责代码质量和学习指导，不重新判断功能对错
- AI不可用/响应非法时只用测试分数
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

## Scoring Rules (与 platform.py 完全一致)

| 情况 | 最终分数 |
|------|----------|
| 语法错误 / 执行失败 / 超时 | **0** |
| test_score < 60 | `final_score = test_score`（AI不参与） |
| test_score >= 60 且AI可用 | `test_score * 0.7 + ai_score * 0.3` |
| test_score >= 60 但AI不可用/响应非法 | `final_score = test_score` |

补充规则:
- AI评分只在 `review_status == "success"` 时生效
- 非法AI响应（score越界/字段类型错误）标记为invalid_response，不参与评分

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific day test
python -m pytest tests/day01_test.py -v
```
