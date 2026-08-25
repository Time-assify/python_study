# Curriculum Review: Day11-Day20（PyTorch核心段）

> 生成于 Curriculum metadata hardening 轮（commit b4d31ac 之后）。
> 本文档仅做内容分析，**不改代码**。下一轮根据本review逐天调整。
>
> 当前统一状态：difficulty=3（规范固定）、estimated_minutes=90~120、
> prerequisites=[]、required_api=[]、hint_levels仅由旧hints自动生成的L1。

## 总体结论

| 维度 | 现状 | 主要问题 |
|------|------|----------|
| 前置知识 | 全部为空 | Day11-20是链式递进段，空prerequisites使学生不知道"今天会用到昨天的什么" |
| Required API | 全部为空 | 与Day01-10标准不一致；学生需读pytest才知道接口（P0-1要解决的问题在此段复现） |
| 提示分级 | 仅L1 | 缺思路(L2)/伪代码(L3)阶梯，卡住时只能求助AI直出答案 |
| 难度标定 | 统一3 | Day13/18/19实际工作量接近CV段的4，建议下一轮校准时保留记录 |

---

## Day11 Dataset/DataLoader — 90min

- **目标**: 掌握数据加载
- **核心任务**: 实现自定义数据集（`__len__`/`__getitem__`、batch切分、transform应用）
- **前置知识应为**: `Tensor`、`nn.Module`（Day08-10）
- **风险**: 变长数据批处理是新手第一道坎；collate_fn在挑战里但核心测试可能隐式依赖默认collate行为
- **建议**: 补required_api（如`SimpleDataset(data, transform=None)`）；prerequisites补Tensor/nn.Module；L2提示给"`__getitem__`返回`(feature, label)`元组"

## Day12 优化器 — 90min

- **目标**: 掌握优化算法
- **核心任务**: optimizer factory（SGD/Adam构建、非法lr报错）+ 小收敛实验
- **前置知识应为**: `Autograd`（zero_grad/step与梯度累积的关系）、Day10 MLP
- **风险**: `zero_grad()`遗漏是经典错误，测试若只看loss下降无法暴露学生对梯度累积的理解
- **建议**: mastery明确"能解释为什么每次step前要zero_grad"；挑战(动量对比)质量好，保留

## Day13 CNN卷积神经网络 — 120min

- **目标**: 理解CNN架构
- **核心任务**: 实现简单CNN（Conv2d+Pool+FC），forward形状正确、反向可传播
- **前置知识应为**: `Dataset/DataLoader`、`卷积/池化`概念、shape计算
- **风险**: **估时最紧张的一天**——手推输出尺寸对无信号处理背景的学生耗时超预期；120min内完成"理解+编码+调试"偏乐观
- **建议**: hints给尺寸公式`out = (in + 2p - k)/s + 1`；考虑把"逐层验证尺寸"从挑战提升为L3伪代码提示

## Day14 BatchNorm/Dropout — 90min

- **目标**: 掌握正则化技术
- **核心任务**: 含BN/Dropout的网络结构 + train/eval行为差异验证
- **前置知识应为**: `CNN前向`、`训练/推理模式`概念
- **风险**: train vs eval差异测试依赖学生正确调用`.eval()`，若测试只查结构则掌握标准落空（现有`test_dropout_train_vs_eval`设计正确，需保持）
- **建议**: prerequisites补"过拟合概念"；mastery加"能说出BN为什么在eval时用滑动统计量"

## Day15 GPU训练 — 90min

- **目标**: 掌握GPU加速
- **核心任务**: device选择、tensor/model搬运、device无关train step
- **前置知识应为**: `训练循环`（Day18之前先学单步，顺序合理）
- **风险**: CI环境无GPU——所有测试必须CPU可跑（现有实现已通过CI验证）；学生本地无GPU时"计时对比"挑战意义有限
- **建议**: 任务描述注明"无GPU环境用CPU完成，重点掌握device抽象"；挑战的计时部分标注可选

## Day16 TensorBoard可视化 — 90min

- **目标**: 掌握训练可视化
- **核心任务**: SummaryWriter创建、scalar写入、幂等close
- **前置知识应为**: `train step`、事件文件概念
- **风险**: **tensorboard包是否在requirements中未确认**；event文件写入在慢磁盘上有延迟
- **建议**: 下一轮核查`requirements.txt`是否含`tensorboard`；90min偏高，可降60~75min（接口面窄）

## Day17 模型检查点 — 90min

- **目标**: 掌握模型保存
- **核心任务**: save/load往返、权重一致、缺失文件报错、epoch元数据恢复
- **前置知识应为**: `state_dict`、`模型结构`、文件序列化基础
- **风险**: load时`map_location`与strict参数容易踩坑；测试已覆盖roundtrip所以方向正确
- **建议**: L3提示给"checkpoint dict建议含model_state/epoch/optimizer_state三键"

## Day18 完整训练框架 — 120min

- **目标**: 构建完整框架
- **核心任务**: train_epoch返回loss、完整收敛流程、evaluate准确率、EarlyStopping(patience/重置/非法值)
- **前置知识应为**: Day11-17全部（这是阶段综合日）
- **风险**: **单日集成度最高**——三个子系统（loop/eval/early-stop）任何一处卡住都会连锁；120min是全课程最紧的之一
- **建议**: prerequisites必须显式列出`["Dataset","DataLoader","optimizer","checkpoint"]`；考虑拆分为"先跑通loop，再加early stop"两步提交路径

## Day19 ResNet残差网络 — 120min

- **目标**: 理解深度网络
- **核心任务**: ResidualBlock（形状保持、非恒等、shortcut梯度流）+ 多块堆叠
- **前置知识应为**: `CNN`（Day13）、`BatchNorm`（Day14）、`nn.Module组合`
- **风险**: 梯度流测试(`gradient_through_shortcut`)是最有价值的测试但也最难调试；瓶颈挑战对当天学生过深（适合保留为挑战不提升）
- **建议**: prerequisites补`["CNN", "BatchNorm"]`；L2提示解释"F(x)+x要求F(x)与x同形，故block末尾卷积要恢复通道数"

## Day20 CIFAR分类 — 90min

- **目标**: 图像分类实战
- **核心任务**: 分类器forward、tiny-batch过拟合验证容量、accuracy/confusion matrix指标
- **前置知识应为**: Day11-19综合（Phase 2收官）
- **风险**: **若测试触发真实CIFAR10下载则不可持续**——需确认测试用合成数据（当前测试名`test_overfit_tiny_batch`暗示合成小批次，下一轮核实）
- **建议**: 明确"数据加载用合成张量模拟，真实CIFAR留给课后"；confusion matrix的行列语义（预测vs真实）在hints中约定

---

## 下一轮执行清单（按优先级）

1. **P0**: Day11-20全部补`required_api`（沿用Day01-10三字段格式）
2. **P0**: Day11-20全部补`prerequisites`（上文逐天清单可直接采用）
3. **P1**: hint_levels补齐L2/L3（上文逐天建议可作为素材）
4. **P1**: 核实day16 tensorboard依赖、day20合成数据声明
5. **P2**: 难度校准讨论——Day13/18/19是否升为4（涉及schema冻结的difficulty分层测试，需一并调整`test_task_schema_types.py::TestDifficultyTiers`）
