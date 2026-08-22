# AI Engineer Training Platform v2.0

一个完整的AI工程师训练学习系统，通过40天训练从Python基础进入AI工程开发。

## 启动学习系统

```bash
python learning_system.py
```

## 系统功能

### 1. 查看每日任务
- 40天结构化学习路径
- 详细的任务描述和要求
- 学习提示和资源

### 2. 提交代码评测
- 代码语法验证
- 自动执行测试
- AI代码审查
- 综合评分

### 3. 查看学习进度
- 进度条可视化
- 各阶段完成情况
- 统计数据

### 4. 查看学习历史
- 提交记录
- 分数变化
- 时间线

### 5. 生成学习报告
- AI生成详细报告
- 保存为Markdown文件

### 6. 查看详细统计
- 薄弱环节分析
- 个性化学习建议

### 7. 搜索知识库
- RAG知识检索
- 相关内容推荐

## 项目结构

```
AI-Engineer-Training/
├── learning_system.py      # 学习系统主程序
├── main.py                 # 命令行入口
├── requirements.txt
├── configs/config.yaml
├── tasks/                  # 40天任务文件
├── submissions/            # 代码提交
├── tests/                  # 测试文件
├── src/
│   ├── task_manager/       # 任务管理
│   ├── submission_manager/ # 提交管理
│   ├── evaluator/          # 代码评估
│   ├── agents/             # AI Agent
│   ├── llm/               # LLM客户端
│   ├── database/          # 数据库
│   ├── rag/               # 知识库
│   └── utils/             # 工具函数
└── data/                  # 数据存储
```

## 40天学习路径

### Phase 1: Python工程 (Day 1-7)
Python基础和工程化开发

### Phase 2: PyTorch (Day 8-18)
PyTorch深度学习框架

### Phase 3: 深度学习 (Day 19-30)
深度学习应用实战

### Phase 4: AI Agent (Day 31-40)
AI智能体开发

## 测试

```bash
python -m pytest tests/ -v
```

## 配置

编辑 `configs/config.yaml` 配置DeepSeek API密钥：

```yaml
deepseek:
  api_key: ${DEEPSEEK_API_KEY}
```