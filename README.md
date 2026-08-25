# AI Engineer Training Platform

A 40-day AI engineer training learning system.

## Current Version: v1.0（课程与平台双冻结）

v1.0 已完成的核心能力：

- **Code Evaluation** — pytest自动化评测：语法/执行/超时判定、跳过感知计分、子进程隔离
- **AI Review** — DeepSeek代码审查：六维度质量分析、schema校验、降级回退
- **Learning Profile** — 学习画像：错误分类统计、知识缺口记录（knowledge_gap_records）、趋势分析
- **40-Day Curriculum** — 课程内容全量收口：
  - D01-10 Python工程基础（含required_api契约与三级hint阶梯）
  - D11-20 PyTorch完整训练工作流（环境体检→数据管线→训练闭环→Debug四工具→毕业项目）
  - D21-30 CV项目路径（图像张量/增强/迁移学习/分类闭环/检测两连/导出服务/CV综合项目）
  - D31-40 LLM与Agent（客户端/prompt/mini-RAG/Planner四环节/sandbox判题/Final Project manifest）

### v2.0 规划方向（未实现，仅规划）

多模态评测扩展、更精细的个性化推荐算法、复习调度（spaced repetition）、
tokenizer体系重引入等。

### 平台功能冻结声明

自 v1.0 起平台功能冻结：**不再新增** RAG / Web界面 / Multi-Agent / 自动课程生成 等
平台级功能，也**不再调整**课程结构（天数/契约签名/估时分层）。
后续仅允许bug级修复；教学路线详见 `docs/final_curriculum_review.md`。

## Quick Start

```bash
# Day01-Day07: 基础依赖
pip install -r requirements.txt

# 进入Day08(PyTorch)前:
pip install -r requirements-pytorch.txt

# View task
python main.py task 1

# Graded hint (level 1/2/3)
python main.py hint 1 --level 1

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
5. **AI Code Review**: DeepSeek analyzes code quality
6. **Get Score**: pytest是功能正确性的核心依据；测试达到60分且AI可用时采用 70% Test + 30% AI；AI不可用或test_score<60时使用test_score；syntax/execution/timeout失败为0。详见下方 Scoring Rules

### answer.py 顶层代码规范（重要）

评测会执行你的 answer.py 并通过 pytest 导入它，因此：

- **模块顶层只定义**：函数、类、常量
- **所有演示/训练/交互代码必须放在入口守卫内**：

```python
def solve(x):
    ...

if __name__ == "__main__":
    # 演示、input()、训练循环、网络请求等只在这里执行
    print(solve(42))
```

- 禁止在顶层调用 `input()`
- Day08以后的PyTorch任务：**禁止import时直接启动训练**
- 顶层长时间阻塞会导致 execution check 超时而直接得0分

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
