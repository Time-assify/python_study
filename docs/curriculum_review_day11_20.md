# Day11-Day20 课程内容审核（Curriculum Content Review）

> 审核基线：v1.0 freeze（aa558d1）。
> 本轮允许：任务JSON内容字段修正、required_api与测试同步。
> 禁止改动：平台代码、Task Schema结构、CLI架构。
> 标注说明：【已应用】=本轮直接修改了 tasks/dayXX.json 或测试文件；
> 【保留观察】=设计合理无需改动；【下轮候选】=需要更多数据再决策。

# Day11

## 当前目标

掌握数据加载。

## 当前任务

实现SimpleDataset(data, labels, transform=None)与make_loader(dataset, batch_size, shuffle=False)。

## 前置知识

Tensor基础、nn.Module前向。【已应用：原为空】

## 预计完成时间

90分钟。【合理，保留】

## 问题

1. prerequisites为空——学生不知道要带着Day08-10的哪些知识进场。
2. required_api为空——接口契约只存在于测试文件头注释。
3. hint_levels是上一轮从旧hints机械生成的，L3"使用transforms进行数据预处理"根本不是伪代码，分级语义完全失效。
4. learn字段缺失。

## 修改建议

- 【已应用】补prerequisites/learn/required_api（从测试契约提取三字段格式）。
- 【已应用】重写hint_levels为真三级阶梯（概念→思路→伪代码），全段统一处理。
- 【保留观察】审核清单要求的Dataset/DataLoader/batch/shuffle/transform五要素在现有测试中全部覆盖（transform参数、shuffle参数均有断言），无需加测。

# Day12

## 当前目标

掌握优化算法。

## 当前任务

实现build_optimizer / step_lr / train_steps三个接口，覆盖优化器分发、学习率调度、完整训练三步曲。

## 前置知识

Autograd梯度、nn.Module前向。【已应用：原为空】

## 预计完成时间

90分钟。【合理，保留】

## 问题

1. 同Day11：prerequisites/required_api缺失、hint分级语义失效。
2. zero_grad遗漏是本日最经典错误，但mastery未显式要求解释其原因。

## 修改建议

- 【已应用】补齐prerequisites/learn/required_api；重写hint_levels。
- 【保留观察】mastery已有"能完成完整的zero_grad-backward-step训练步"，语义达标。
- 【保留观察】挑战（SGD+Momentum对比Adam收敛）边界克制，无过度扩展。

# Day13

## 当前目标

理解CNN架构。

## 当前任务

实现SimpleCNN(num_classes=10)与count_conv_layers(model)；【已应用】新增训练冒烟要求——固定小批次上SGD+交叉熵迭代数十步loss明显下降。

## 前置知识

Dataset/DataLoader使用、优化器训练三步曲。【已应用：原为空】

## 预计完成时间

120分钟。【合理，保留——含新增训练冒烟后此估时刚好]

## 问题

1. 审核清单明确要求CNN日必须包含loss/optimizer/backward/training loop，
   而原测试只验证结构（卷积层计数、池化存在）与前向形状+单次backward，
   "搭好网络却不会训练"也能满分通过——这正是清单警告的反模式。
2. train()/eval()模式切换无任何覆盖。
3. 同段共性问题：prerequisites/required_api/hint分级缺失。

## 修改建议

- 【已应用】tests/day13_test.py新增TestTrainingSmoke类（2个测试）：
  - test_train_reduces_loss：固定batch 30步SGD，final < initial * 0.9
  - test_optimizer_step_updates_params：step()后参数必须实际变化
  不新增answer.py接口——复用SimpleCNN，训练循环写在测试内部。
- 【已应用】day13 skills补充pytorch.optimizer/pytorch.training_loop并同步类标记；
  tests[]经AST重新同步（6→8）；core_task/mastery同步加入训练冒烟与train/eval切换。
- 【保留观察】train/eval的"行为差异"验证留给Day14（BN/Dropout才有行为差异可测），
  Day13只要求会调用切换。

# Day14

## 当前目标

掌握正则化技术。

## 当前任务

实现NetWithReg(in_features, num_classes, p_drop=0.5)，含BatchNorm1d与Dropout。

## 前置知识

CNN结构基础、forward形状验证。【已应用：原为空】

## 预计完成时间

90分钟。【合理，保留】

## 问题

1. 同段共性问题：前置/API/hint缺失。
2. 单接口一天略薄，但train/eval行为差异验证有一定调试量，90分钟成立。

## 修改建议

- 【已应用】补齐prerequisites/learn/required_api/hint_levels。
- 【保留观察】test_dropout_train_vs_eval精准命中本日核心能力，质量高。
- 【保留观察】审核清单的validation/overfitting/lr/checkpoint四要素分布检查：
  lr在Day12、checkpoint在Day17、validation在Day18、overfitting观察在
  本日挑战（方差扫描）与Day20（单批过拟合）——链条完整，无需重排。

# Day15

## 当前目标

掌握GPU加速。

## 当前任务

实现get_device / move_to_device / train_step(model, x, y, device)。

## 前置知识

训练循环概念、loss与optimizer关系。【已应用：原为空】

## 预计完成时间

90分钟。【偏松，但device抽象对新手有认知成本，保留】

## 问题

1. 同段共性问题：前置/API/hint缺失。
2. 无GPU环境下计时对比挑战意义有限。

## 修改建议

- 【已应用】补齐四件套；hint L3给出device无关训练的伪代码骨架。
- 【保留观察】所有测试CPU可跑（CI实证），设备抽象本身即本日知识点。

# Day16

## 当前目标

掌握训练可视化。

## 当前任务

实现get_writer(logdir) / log_metrics(writer, step, metrics) / close_writer(writer)。

## 前置知识

训练单步概念、device概念。【已应用：原为空】

## 预计完成时间

60分钟。【已应用：90→60——三个小函数撑不起90分钟】

## 问题

1. 同段共性问题：前置/API/hint缺失。
2. torch.utils.tensorboard运行时依赖tensorboard包，而requirements-pytorch.txt
   只声明了torch/torchvision——真实评分环境会ImportError。
3. 估时虚高（见上）。

## 修改建议

- 【已应用】requirements-pytorch.txt追加tensorboard>=2.10。
- 【已应用】estimated_minutes降为60；补齐四件套。

# Day17

## 当前目标

掌握模型保存。

## 当前任务

实现save_checkpoint / load_checkpoint / restore_model三件套。

## 前置知识

state_dict与模型结构、文件序列化基础。【已应用：原为空】

## 预计完成时间

90分钟。【合理，保留——state_dict严格加载与异常路径有调试量】

## 问题

1. 同段共性问题：前置/API/hint缺失。

## 修改建议

- 【已应用】补齐四件套；hint L3明确"权重+epoch打包、缺失抛异常"两个关键约定。
- 【保留观察】Top-K checkpoint挑战边界克制（不引入新框架概念），保留。

# Day18

## 当前目标

构建完整框架。

## 当前任务

实现train_one_epoch / evaluate / EarlyStopping(patience, min_delta)。

## 前置知识

DataLoader批处理、optimizer与scheduler、checkpoint。【已应用：原为空】

## 预计完成时间

120分钟。【合理，保留——这是Phase 2的综合日】

## 问题

1. 全段最高集成度的一天，但三个子系统（loop/eval/early-stop）内聚于
   "训练框架"单一主题，不属于审核清单警告的"数据处理+模型设计+训练+
   调参+部署"多主题混杂，无需拆分。
2. 平均loss的加权口径（按样本数 vs 按batch数）是隐蔽坑点，原提示未覆盖。

## 修改建议

- 【已应用】补齐四件套；hint L2显式提示加权口径陷阱。
- 【保留观察】EarlyStopping的patience/min_delta/重置语义已被三个测试精确锁定。

# Day19

## 当前目标

理解深度网络。

## 当前任务

实现ResidualBlock(channels)（shape保持）与SimpleResNet（≥2个残差块）。

## 前置知识

CNN卷积尺寸计算、BatchNorm、nn.Module组合。【已应用：原为空】

## 预计完成时间

120分钟。【合理，保留——梯度流调试是硬时间】

## 问题

1. 同段共性问题：前置/API/hint缺失。
2. test_quick_training_step已覆盖训练维度，无需再加训练测试。

## 修改建议

- 【已应用】补齐四件套；hint L2/L3强调shape守恒判据与捷径梯度回传。
- 【保留观察】bottleneck瓶颈结构挑战深度合适（只对比参数量，不要求训练SOTA），
  属克制的可选扩展。

# Day20

## 当前目标

图像分类实战。

## 当前任务

实现CIFARNet((B,3,32,32)) / accuracy(top-1) / confusion_matrix；过拟合冒烟实验在挑战位。

## 前置知识

训练循环、评估指标概念、数据增强意识。【已应用：原为空】

## 预计完成时间

120分钟。【已应用：90→120——Phase收官日需网络+双指标+冒烟实验】

## 问题

1. 提示里出现"使用torchvision.datasets.CIFAR10"，但测试头明确声明
   无需下载数据集——提示误导学生去下载150MB数据集。
2. accuracy/confusion_matrix的行列与长度约定是实现歧义高发区，原提示未约定。
3. 同段共性问题：前置/API/hint缺失。

## 修改建议

- 【已应用】hint_levels重写：L2固定混淆矩阵"行为真实、列为预测"约定；
  L3给出完美预测判据与长度不一致报错要求。
- 【已应用】estimated_minutes升为120；补齐四件套。
- 【保留观察】数据集合成化已在测试层解决（无需下载），本轮仅修掉误导性提示。

---

## 段级结论（Day11-20）

| 审核项 | 结论 |
|--------|------|
| 时间合理性 | Day16 90→60、Day20 90→120，其余维持 |
| 前置知识 | 十天全部补齐，链式递进（Tensor→训练→正则→设备→可视化→保存→框架→ResNet→实战） |
| 任务与测试匹配 | required_api全部从测试头注释提取为三字段契约；Day13补2个训练冒烟测试并AST同步 |
| Challenge边界 | 十天挑战均未越界（无新框架概念、无可评分扩张），全部保留 |
| Mastery对应能力 | Day13增补训练冒烟与模式切换两条；其余与测试断言对齐良好 |
| 依赖修复 | requirements-pytorch.txt补tensorboard（Day16真实环境必需） |

**遗留到下一轮（Day21-30审核）的观察项：**
- hint_levels的L3仍以"伪代码/判据"为主，是否引入更细的局部代码片段级别待讨论；
- Day20的accuracy除零口径（空输入）当前测试未覆盖，可作为Day21-30指标类任务的通用检查项。
