# Final Curriculum Review — Day01-Day40 全量终检

> 基线：b1fd92e之后的final polish轮。本文件为v1.0冻结前的最后一份全量体检报告。
> 检查维度：Goal / Estimated Time / Prerequisites / Core Task / Risk。

## 一、全量速览表

| Day | 标题 | Goal | 估时(难度) | 前置知识 | Core Task | Risk |
|-----|------|------|-----------|---------|-----------|------|
| D01 | Python工程环境 | 掌握项目结构 | 60min (diff 1) | （无——入门日） | 实现create_project_structure / create_config_file / setup_logger三个函数（接口见Required A… | 首个任务，环境搭建耗时易超预期 |
| D02 | 高级Python | 掌握装饰器、生成器 | 60min (diff 2) | 函数与闭包; 可迭代对象 | 实现repeat / memoize / fibonacci / chunked四个接口，以及低门槛版Timer（只需with Timer():正常运行） | 装饰器/生成器抽象度高；Timer已降为低门槛 |
| D03 | 面向对象设计 | 设计ML框架基类 | 60min (diff 2) | Python类与继承 | 设计ML框架基类结构：BaseModel/LinearModel/OptimizerBase（见Required API） | 常规风险 |
| D04 | 多线程多进程 | 掌握并发编程 | 60min (diff 2) | 函数作为参数; 列表推导 | 使用ThreadPoolExecutor实现并发任务执行器：run_in_threads / concurrent_map | 常规风险 |
| D05 | API客户端开发 | 掌握HTTP客户端 | 60min (diff 2) | Python字典; 异常处理 | 实现build_url与APIClient(get/post)，并把requests异常包装为APIError（不含重试） | 真实HTTP不可依赖——测试全部离线模拟 |
| D06 | NumPy/Pandas数据处理 | 掌握数据处理 | 90min (diff 3) | Python字典与列表; 基本统计概念 | 实现clean_dataframe与minmax_normalize（Pandas为主，NumPy数值辅助） | 常规风险 |
| D07 | Mini ML Framework | 构建简单ML框架 | 90min (diff 3) | NumPy array与shape; 均值与平方; 函数/类基础 | 实现mse_loss与LinearRegression(fit/predict)，在y=2x+1数据上收敛（建议：理论推导20min → 编码50min → 调… | 数学推导+首次梯度下降，认知负荷最高的一天(90min) |
| D08 | Tensor基础 | 掌握Tensor操作 | 90min (diff 2) | Python slicing; NumPy shape | 实现常见Tensor操作 | 常规风险 |
| D09 | Autograd自动微分 | 理解自动微分 | 90min (diff 3) | Tensor; 函数求导基本概念 | 实现梯度计算 | 常规风险 |
| D10 | nn.Module神经网络 | 构建神经网络 | 90min (diff 3) | Tensor; Autograd; Python class继承 | 实现多层感知机 | 常规风险 |
| D11 | PyTorch Tensor基础 | 夯实张量与自动求导基础 | 90min (diff 3) | Python slicing; NumPy shape概念 | 实现tensor_info / to_device / grad_of_quadratic / grad_after_two_backwards四个接口（不涉及… | 主题重写日：张量综合，注意与Day08-09的衔接复述 |
| D12 | Dataset/DataLoader | 掌握数据加载管线 | 90min (diff 3) | Tensor基础; 简单网络前向 | 实现SimpleDataset与make_loader（接口见Required API） | 常规风险 |
| D13 | CNN卷积神经网络 | 理解CNN架构 | 120min (diff 3) | Dataset/DataLoader使用; 优化器训练三步曲 | 实现SimpleCNN/count_conv_layers、训练闭环API build_optimizer / step_lr / train_one_epoc… | 首次完整训练闭环，训练冒烟对新手是质变 |
| D14 | BatchNorm/Dropout | 掌握正则化技术 | 90min (diff 3) | CNN结构基础; forward形状验证 | 实现NetWithReg正则化网络，以及train_validation_split / evaluate_accuracy验证闭环（train/val划分互斥… | 常规风险 |
| D15 | 训练Debug能力 | 会找训练问题，而不是训练更大模型 | 90min (diff 3) | CNN训练闭环; 正则化层与验证 | 实现四个诊断接口：assert_matmul_compatible / check_gradient_flow / is_eval_deterministic … | Debug主题新设，诊断思维需要示范引导 |
| D16 | TensorBoard可视化 | 掌握训练可视化 | 60min (diff 3) | 训练单步概念; device概念 | 实现训练过程可视化 | tensorboard依赖已在requirements-pytorch声明 |
| D17 | 模型检查点 | 掌握模型保存 | 90min (diff 3) | state_dict与模型结构; 文件序列化基础 | 实现模型检查点 | 常规风险 |
| D18 | 完整训练框架 | 构建完整框架 | 120min (diff 3) | DataLoader批处理; optimizer与scheduler; checkpoint | 实现完整训练流程（核心约90分钟内完成，进阶内容见optional_challenge） | Phase2集成度最高：loop/eval/early-stop三件套 |
| D19 | ResNet残差网络 | 理解深度网络 | 120min (diff 3) | CNN卷积尺寸计算; BatchNorm; nn.Module组合 | 实现ResNet块（核心约90分钟内完成，进阶内容见optional_challenge） | 常规风险 |
| D20 | CIFAR分类与Phase毕业项目 | 图像分类实战 | 120min (diff 3) | 训练循环; 评估指标概念; 数据增强意识 | 实现build_dataset_loaders（合成可分两类(3,32,32)数据，train/val互斥划分）与train_and_validate（完整训练… | 毕业小项目：端到端+可视化产物 |
| D21 | 数据增强 | 掌握数据增强 | 120min (diff 4) | （无——入门日） | 实现数据增强（核心约90分钟内完成，进阶内容见optional_challenge） | 常规风险 |
| D22 | 迁移学习 | 掌握迁移学习 | 120min (diff 4) | CNN训练闭环; state_dict与参数遍历 | 理解迁移学习流程并实现freeze_backbone/unfreeze_all/extract_features。核心是掌握冻结-特征提取-按需解冻的流程；大型… | 迁移学习闸门：防止直接上手大模型微调 |
| D23 | 图像分类数据集与训练闭环 | 把CV基础能力串成第一个完整分类训练 | 90min (diff 4) | CNN训练闭环; 正则化与验证; checkpoint概念 | 实现make_color_samples / ImagesDataset / cnn_baseline / train_classifier四件套，完成合成彩色… | 主题重写日(NLP→CV分类闭环)，tokenization已退役至Phase4按需 |
| D24 | Transformer | 理解Transformer | 120min (diff 4) | 线性层与softmax; 序列数据概念 | 实现Transformer块（核心约90分钟内完成，进阶内容见optional_challenge） | 序列建模桥梁日，服务Phase4，CV主线不依赖 |
| D25 | HuggingFace | 掌握HuggingFace | 120min (diff 4) | attention机制; padding与mask概念 | 使用HuggingFace库（核心约90分钟内完成，进阶内容见optional_challenge） | 常规风险 |
| D26 | YOLO目标检测 | 理解目标检测 | 120min (diff 4) | 边界框编码[x1,y1,x2,y2]; 滑窗与网格概念 | 实现YOLO检测（核心约90分钟内完成，进阶内容见optional_challenge） | 检测概念密集：anchor/IoU/NMS纯几何实现 |
| D27 | 目标检测实战 | 目标检测应用 | 120min (diff 4) | bbox/IoU/NMS(D26); AP指标定义 | 核心必做： - 实现DetectionDataset - 理解box格式(xyxy) - 实现/理解average_precision计算 - 使用合成小数据完… | 常规风险 |
| D28 | ONNX模型导出 | 掌握模型导出 | 120min (diff 4) | CNN模型结构; 推理与训练模式差异 | 导出ONNX模型（核心约90分钟内完成，进阶内容见optional_challenge） | onnx/onnxruntime依赖已声明 |
| D29 | FastAPI部署 | 掌握模型部署 | 120min (diff 4) | 模型推理调用; HTTP请求响应基础 | 部署模型API（核心约90分钟内完成，进阶内容见optional_challenge） | 常规风险 |
| D30 | CV阶段综合项目 | 独立完成 数据→模型→训练→评价→结果展示 的完整小项目 | 120min (diff 4) | CNN训练闭环; checkpoint保存恢复; yaml配置读写 | 实现TrainConfig(yaml持久化)/make_loaders/build_model/run_pipeline。run_pipeline按配置执行全链… | CV毕业项目：配置驱动+最优权重落盘+可复现断言 |
| D31 | LLM客户端 | 掌握LLM API | 120min (diff 3) | requests/httpx使用; 重试与超时概念 | 核心必做： - LLMClient(api_key/transport)与is_available - chat_stream流式yield(mock tran… | transport注入模式首次出现——离线模拟真实API的关键设计 |
| D32 | Prompt Engineering | 掌握提示工程 | 120min (diff 3) | LLM消息结构与角色; 指令清晰化技巧 | 设计有效提示（核心约90分钟内完成，进阶内容见optional_challenge） | 常规风险 |
| D33 | RAG检索增强生成 | 理解RAG架构 | 120min (diff 3) | 向量与余弦相似度; 文本切分概念 | 实现RAG系统（核心约90分钟内完成，进阶内容见optional_challenge） | mini-RAG关键词版，刻意回避向量库复杂度 |
| D34 | Agent框架 | 构建Agent框架 | 120min (diff 4) | 函数式工具封装; 字典驱动的配置 | 实现Tool/Agent/Memory与plan_step规划器，形成Tool→Planner→Execution→Memory四环节闭环（不是简单的while… | Planner环节新增：规则匹配而非LLM调用 |
| D35 | Tool Calling | 掌握工具调用 | 120min (diff 4) | JSON Schema思想; 严格类型校验 | 实现工具调用（核心约90分钟内完成，进阶内容见optional_challenge） | 常规风险 |
| D36 | Code Agent | 构建代码Agent | 120min (diff 4) | AST基础; 代码风格常见问题 | 实现代码生成Agent（核心约90分钟内完成，进阶内容见optional_challenge） | 代码生成/审查双能力，AST处理较抽象 |
| D37 | 自动评测平台 | 构建评测系统 | 120min (diff 4) | 沙箱与超时机制; 评分口径设计 | 实现自动评测平台（核心约90分钟内完成，进阶内容见optional_challenge） | 沙箱安全语义需准确(禁止__import__/open) |
| D38 | AI学习导师 | 构建学习导师 | 120min (diff 4) | 均值与趋势判断; 阈值过滤 | 实现AI学习导师（核心约90分钟内完成，进阶内容见optional_challenge） | 常规风险 |
| D39 | Agent系统整合 | 整合Agent系统 | 120min (diff 4) | 发布订阅模式; 健康检查语义 | 实现Agent系统整合（核心约90分钟内完成，进阶内容见optional_challenge） | 常规风险 |
| D40 | Final Project | 完成最终项目 | 180min (diff 5) | D11-D39综合能力 | 核心必做： - register_student注册学生 - submit_result保存提交与错误 - get_profile历史统计(error_stat… | Capstone：project_manifest强制工程结构申报 |

## 二、重点发现

### 1. 是否超过2小时

超过120分钟的日期：**D40**

其中 D40(180min) 为capstone特例（分阶段推进，每阶段约90分钟）；
其余120分钟日均满足"核心≈90分钟 + optional_challenge进阶30分钟"拆分原则，
挑战位承载：D13尺寸推导、D18 LR组合、D19 bottleneck、D22差分微调、
D27 PR深挖、D30增强开关对比等。

### 2. 是否缺前置知识

前置为空的日期：**D21**（D1为入门日，属合理空缺）。
D11-D40共40天的prerequisites在历轮review中逐段补齐：
D21-30(CV路径)与D31-40(LLM/Agent路径)于本轮完成最后一遍填空。

### 3. 是否任务描述不清

description长度<15字符的日期：**无**
所有40天均具备完整description；core_task自Round起统一携带
"接口见Required API"指引与（≥90分钟日的）时间预算标注。

## 三、分段能力结论

| 阶段 | 天数 | 收口能力 |
|------|------|---------|
| Python工程基础 | D01-D10 | 项目结构/高级语法/OOP/并发/API/数据/线性回归/Tensor入门 |
| PyTorch训练能力 | D11-D15 | 张量体系→数据管线→CNN闭环→验证→**Debug四工具** |
| 训练工程化 | D16-D20 | 可视化/checkpoint/框架/ResNet/**CV毕业项目** |
| CV项目路径 | D21-D30 | 图像张量/增强/迁移学习/分类闭环/检测两连/导出/服务/**CV综合项目** |
| LLM应用 | D31-D33 | 客户端(streaming/retry/json)/prompt/mini-RAG五环节 |
| Agent系统 | D34-D39 | Tool/Planner/Execution/Memory/沙箱判题/分析/系统集成 |
| Capstone | D40 | 平台闭环 + **manifest工程结构申报** |

## 四、冻结声明

本轮之后课程内容进入冻结：不再调整天数安排、契约签名与估时分层；
后续仅允许bug级修复。平台侧维持v1.0 freeze不变。
