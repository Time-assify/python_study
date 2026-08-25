# Changelog

All notable changes to this project are documented here.

## [1.0.0] - 2026-08-25

Initial release of the AI Engineer Training Platform.

### 平台能力（Platform）

- **Automated Evaluation**
  - 每日任务由pytest契约测试驱动；语法错误/执行失败/超时一律0分
  - 跳过感知计分：skip不计入分母，防止"空实现刷分"
  - 子进程隔离评测：`--basetemp`+受控环境变量，杜绝本地状态污染
- **AI Code Review（DeepSeek）**
  - 六维度质量分析（无key自动降级为纯pytest评分）
  - 响应schema校验：非法结构标记`invalid_response`且不参与加权
  - test_score≥60且AI可用时按 70% test + 30% AI 合成final score
- **Learning Profile**
  - 统一数据模型：LearningRecord / StudentProfile / ReviewResult / EvaluationResult
  - ErrorClassifier十三类错误归因；trend(improving/stable/declining)判定
  - knowledge_gap_records表：测试失败→skill→KnowledgePoint自动绑定计数
  - 连击难度推荐：连败≥2降难度、连胜≥3升难度
- **CLI**
  - `task DAY [--detail]` 分层展示（默认五要素+核心任务；detail含hints/资源/知识点）
  - `hint DAY --level 1|2|3` 三级提示（概念/思路/伪代码），禁止直接给完整答案
  - `submit / progress / report / start` 完整学习回路

### 课程内容（Curriculum, 40天）

- **D01-D10 Python工程基础**：项目结构、装饰器/生成器/上下文管理器、OOP抽象、
  线程池、API客户端、Pandas清洗、线性回归梯度下降（90min含推导）
- **D11-D20 PyTorch完整训练工作流**：张量体系与环境体检 → Dataset/DataLoader →
  CNN完整闭环(build_optimizer/step_lr/train_one_epoch/fit_classifier) →
  正则化+validation铁律(参数快照检查) → Debug四工具 → TensorBoard/checkpoint/
  完整框架/ResNet/**CV毕业小项目**
- **D21-D30 CV项目路径**：HWC→CHW图像张量、增强三件套、迁移学习闸门、
  分类闭环(权重落盘可复现)、Transformer/HF桥梁、检测概念两连(anchor/IoU/NMS→AP)、
  ONNX导出、FastAPI服务、**CV综合项目**(配置驱动+可视化产物)
- **D31-D40 LLM与Agent**：LLM客户端(streaming/retry/json)、prompt工程、
  mini-RAG五环节(prompt组装衔接生成)、Tool/Planner/Execution/Memory、
  工具schema严格校验、代码生成与审查、沙箱判题、学习分析、系统集成、
  **Final Project**(manifest强制src/tests/README/requirements工程交付)

### 课程基础设施

- 知识点注册表 `config/knowledge_points.yaml`（85条：id/name/category/level），
  Task skills、测试marker、Profile记录三方统一引用
- 每日标准schema：difficulty(1-5)/estimated_minutes/prerequisites/learn/
  review_points/required_api{name,signature,description}/mastery/
  optional_challenge/hint_levels[{level,content}]/environment_notes/required_output
- hint质量分级检查：L1禁代码、L2禁完整实现、L3允许伪代码禁完整答案
- 全部数据合成化/离线化：零真实数据集下载，CPU可完成所有核心任务
- 测试纪律：fail-not-skip机制、tautological assertion扫描、训练步数有界、
  challenge目录与主评分隔离

### 文档

- `docs/final_curriculum_review.md` — 40天全量终检报告（连续学习可行性确认）
- `docs/curriculum_review_day11_20.md` / `_day11_20_final.md` — PyTorch段三轮审核存档
- `docs/curriculum_review_day21_30.md` — CV段审核存档

[1.0.0]: https://github.com/Time-assify/python_study/releases/tag/v1.0
