# Day11-Day20 课程内容审核（Curriculum Content Review）

> 审核基线：v1.0 freeze（aa558d1）。
> 本轮允许：任务JSON内容字段修正、required_api与测试同步。
> 禁止改动：平台代码、Task Schema结构、CLI架构。
> 标注说明：【已应用】=本轮直接修改了 tasks/dayXX.json 或测试文件；
> 【保留观察】=设计合理无需改动；【下轮候选】=需要更多数据再决策。

---

# Round3（完整PyTorch学习工作流）

## 修改原因总述

Round2解决了"顺序"问题，本轮解决"能力闭环"问题：Phase2结束时学生应具备
**环境判断→数据管线→全链训练→评估判读→故障排查** 的完整深度学习训练能力，
而不是零散API操作。逐日定位：

| 日 | Round2状态 | 本轮补齐 |
|----|-----------|---------|
| D11 | 张量四接口（无环境意识/无排错） | +环境体检check_environment、+shape冲突定位checked_matmul |
| D12 | 数据管线核心 ✓ | transforms三件套边界显式化（仅ToTensor/Normalize/RHF，防复杂增强蔓延） |
| D13 | 训练闭环但loader外置 | +fit_classifier串起Dataset→…→Validation全链 |
| D14 | split+accuracy ✓ | +record_loss_curve曲线记录与首尾判读；+checkpoint挑战预习 |
| D15 | 设备/GPU日（与D11新环境能力重复） | **主题重写：训练Debug能力**——shape检查/梯度体检/train-eval实证/loss不下降诊断 |

关键决策说明：
1. **D15主题替换的理由**：device迁移与单步训练已被D11(to_device/check_environment)
   与D13(train_one_epoch/fit_classifier)覆盖，原D15内容沦为重复练习；
   而Debug是清单明确要求且此前完全缺失的一等能力。
   原get_device/move_to_device契约退役，pytorch.device技能归属移至Day11。
2. **确定性验证策略延续**：fit_classifier用lr=0冻结参数的手工均值等价验证；
   record_loss_curve用可分合成数据断言首尾比，避免随机收敛带来的flaky。

## 逐日变更

### Day11【已应用】

- 新增required_api：`check_environment()`（cuda_available/device_count/torch_version/
  default_device四键；无CUDA时默认设备必须cpu——最常见环境误判）、
  `checked_matmul`（不兼容抛ValueError且消息含两个完整shape）。
- 新增TestEnvironmentCheck(2)/TestShapeDebug(2)测试；tests[]同步8→12。
- mastery按规范追加："能够定位基础Tensor维度和device问题"。

### Day12【已应用】

- optional_challenge与learn显式圈定transforms可选范围：
  **ToTensor / Normalize / RandomHorizontalFlip三件套**，
  并注明深入增强不在本阶段（防scope creep）。
- collate_fn padding挑战保留（与transforms边界互不冲突）。

### Day13【已应用】

- required_api追加`fit_classifier(model, train_loader, val_loader, epochs, lr)`
  返回{train_loss, val_loss, val_acc}——把Dataset→DataLoader→CNN→Loss→
  Optimizer→Backward→loop→Validation八环节收束成一个可调用入口。
- TestFullPipeline(3)：结构/取值范围、lr=0手工均值等价（确定性）、
  可分二类任务10 epoch val_acc≥0.75（真实学习发生）。
- mastery按规范追加："能够完成最小图像分类训练pipeline"；description写入
  八环节管线图。skills追加pytorch.dataloader/evaluation.accuracy；tests[] 13→16。

### Day14【已应用】

- required_api追加`record_loss_curve(model, x, y, epochs, lr)`→list[float]；
  TestLossCurve(2)：长度+有限非负、可分数据首尾比<0.7的下降判读。
- mastery追加loss curve首尾判读；optional_challenge追加checkpoint预习
  （保存最优epoch并恢复一致），正式课仍在Day17。

### Day15【已应用·主题重写】

原"GPU训练"整日替换为**训练Debug能力**：

| 接口 | 排查目标 | 测试要点 |
|------|---------|---------|
| assert_matmul_compatible(a,b) | shape冲突 | 兼容静默；冲突报错消息必含双方shape |
| check_gradient_flow(model,x,y) | 梯度健康 | has_gradients/num_params/max_abs_grad；全零输入不崩 |
| is_eval_deterministic(model,x,mode) | train/eval区别 | Dropout模型eval确定/train随机(p=0.9实证)/纯线性恒确定 |
| diagnose_loss_history(losses) | loss不下降 | decreasing/flat/increasing三分；flat与increasing必须附排查建议 |

共12测试全部CPU确定性。skills=[tensor_shape/autograd/training_step/training_loop]
（device归属已移交Day11）。mastery四条对应四类故障。

### Day16-Day20（P1-2复核）

沿用Round2结论：五天均已满足"核心pipeline/挑战优化"拆分原则
（D18 LR组合、D19 bottleneck、D20过拟合实验均在挑战位），本轮零改动。【保留观察】

---

# Round2（PyTorch学习路线重排）

## 修改原因总述

Round1之后路线为：数据加载→优化器→CNN→正则化→设备→可视化→保存→框架→ResNet→实战。
本轮按"P0-1重构学习顺序"要求调整为：

```
D11 Tensor基础(dtype/device/shape/requires_grad/backward)   ← 新增综合收敛日
D12 Dataset/DataLoader                                       ← 原D11后移一天
D13 CNN + 完整训练闭环(含build_optimizer/step_lr/train_one_epoch) ← 原D12优化器并入
D14 正则化 + train/validation split                          ← P0-3验证闭环
D15 设备/GPU训练 (+checkpoint挑战预习)                        ← P1-1
D16-D20 不变（TensorBoard/检查点/完整框架/ResNet/CIFAR）
```

理由：
1. **张量知识此前分散在Day08/09**，学生进入Phase2时缺少一个统一收敛点；
   dtype/device/shape/requires_grad/backward五件事放在同一天形成完整心智模型，
   避免后面每个新概念都要回补张量细节。
2. **独立优化器日被取消**：脱离具体模型的SGD/Adam练习过于抽象；将其并入CNN
   训练闭环（P0-2），在"让网络真正学起来"的语境下学习optimizer与scheduler。
   StepLR随迁至Day13，避免技能丢失（pytorch.lr_scheduler归属day13）。
3. **数据加载紧随张量日**：先会操作单个张量，再学怎么批量喂给模型，符合
   "单元→管线"的认知顺序。

## 逐日变更

### Day11（内容重写：Dataset → Tensor基础）

- 问题：原Day11跳过张量体系直接进数据管线；dtype/device/requires_grad散落各天无收敛点。
- 【已应用】tests/day11_test.py重写：tensor_info(shape/dtype/device三键)、
  to_device、grad_of_quadratic(已知值13断言)、grad_after_two_backwards(累积语义6.0断言)，
  共8测试；skills=[pytorch.tensor/tensor_shape/device/autograd]；tasks/day11.json全量重写。

### Day12（内容迁移：承接原Day11数据加载）

- 问题：数据管线应晚于张量综合日。
- 【已应用】tests/day12_test.py承接原Day11全部7个Dataset/DataLoader测试（仅换header）；
  tasks/day12.json继承SimpleDataset/make_loader契约、hint阶梯与collate_fn挑战；
  prerequisites改为["Tensor基础","简单网络前向"]。

### Day13（P0-2：完整训练闭环）

- 问题：上轮补的训练冒烟只证明"能学"，但优化器构建/调度/epoch级mini-batch循环
  没有API契约——学生可以用测试外硬编码绕过。
- 【已应用】required_api追加build_optimizer / step_lr / train_one_epoch三条契约；
  tests/day13_test.py新增TestTrainingAPI类5个测试：
  - build_optimizer分发(sgd/adam)与非法拒绝(未知名、lr<=0)
  - step_lr两周期衰减精确到gamma倍
  - train_one_epoch用lr=0冻结参数的手工均值等价验证（确定性，不依赖随机收敛）
  - 尾批(n=7,batch=3)边界正常返回有限loss
  skills追加pytorch.lr_scheduler；tests[] AST同步8→13；mastery/learn/core_task同步。

### Day14（P0-3：Validation闭环）

- 问题：验证集概念此前缺席直到Day18才出现；正则化效果恰恰需要在"独立验证集"
  上观察才有说服力——本日是引入validation的天然位置。
- 【已应用】required_api追加train_validation_split(互斥+全覆盖+max(1,int(n*ratio))契约)
  与evaluate_accuracy(top-1)；tests/day14_test.py新增TestValidationSplit类5个测试
  （尺寸/最小1条/互斥覆盖/已知值0.75/区间约束）；skills追加evaluation.accuracy与
  pytorch.training_loop；mastery加入"validation为何必须独立于训练集"。
- 【保留观察】不引入复杂指标（F1/AUC等），accuracy足够。

### Day15（P1-1：checkpoint概念预习）

- 问题：checkpoint正式课在Day17，但torch.save/load作为通用技能可以提前接触。
- 【已应用】optional_challenge追加"挑战预习"条目（save state_dict→load恢复一致），
  明确标注正式深入在Day17。核心任务不变（device抽象仍是本日主体）。

### Day16-Day20（P1-2：负担审计结论）

逐日核对"核心完成pipeline、挑战负责优化"原则：

| 日 | 核心分钟 | 审计结论 |
|----|---------|---------|
| D16 TensorBoard | 60 | 合规 |
| D17 checkpoint | 90 | 合规 |
| D18 完整框架 | 120 | 合规——三子系统内聚于单一主题，Top-K/LR组合已在挑战位 |
| D19 ResNet | 120 | 合规——bottleneck性能对比已在挑战位 |
| D20 CIFAR | 120 | 合规——过拟合容量实验已在挑战位 |

无需拆分。【保留观察】

### environment_notes（P1-3）

- 【已应用】Day11-Day20全部新增environment_notes字段（纯JSON内容层，
  Task dataclass/CLI未动，schema冻结保持）：CPU可完成性声明、GPU可选说明、
  tensorboard依赖提示、合成数据声明。

## 回归影响

- pytest 762 passed, 318 skipped（新增11个测试全部通过，含确定性avg-loss等价验证）
- 技能注册表零孤儿：dataset/dataloader归day12、optimizer/lr_scheduler归day13，
  union不变；marker⊆task.skills双向校验通过
- 估时分层快照不受影响（所有minutes保持原tier值）

---
以下为Round1逐日审核存档。

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
