# Day11-Day20 最终收口（PyTorch Curriculum Final Polish）

> 基线：61dc029（Round3之后）。本轮为Phase 2最后收口。
> 平台/Evaluator/Schema/AI Agent零改动；所有变更限于任务JSON内容、
> 测试文件、知识点注册表内容项。

## 本轮变更清单

| 项 | 内容 | 落点 |
|----|------|------|
| P0-1 | Day13 `required_output`四产物，杜绝"只交类定义不训练" | tasks/day13.json |
| P0-2 | validation铁律：`validate_model`参数快照检查+口径mastery | day14.json + day14_test.py(3测) |
| P0-3 | Debug落地：`debug_training_issue`四病例三段式分诊 | day15.json + day15_test.py(3测) |
| P1-1 | transforms边界复核：仅ToTensor/Normalize/RHF ✓ | 无改动，确认 |
| P1-2 | D16-20规模复核：核心均≤90min语义成立，重活已在挑战位 | 文档声明 |
| P1-3 | 注册表补`pytorch.validation`/`pytorch.debugging`(共83条) | config/knowledge_points.yaml |
| P1-4 | Day20毕业小项目：build_dataset_loaders + train_and_validate | day20.json + day20_test.py(4测) |

### P0-2 实现说明：如何"检查学生没在validation里step"

新增契约 `validate_model(model, val_loader, loss_fn=None) -> {'loss','acc'}`：
签名本身**不含optimizer**；测试用参数快照铁律——调用前后逐参数
`torch.equal`必须全真。等价于证明validation阶段没有发生任何
optimizer.step或手动更新。另附no_grad性能粗检（256样本<5s）。

### P0-3 实现说明：debug分诊的验收口径

`debug_training_issue(case)`覆盖四病例：shape_mismatch / grad_not_cleared /
missing_eval_switch / loss_not_decreasing。返回{issue, symptom, fix}；
fix必须命中动作关键词（zero_grad/eval/shape/lower learning rate），
空话建议直接判负；未知病例必须ValueError。
配合Round3已有的四个动手诊断工具（形状/梯度/模式/曲线）形成
"工具实操 + 分诊知识"双层能力。

### P1-4 毕业小项目设计

Day20在原CIFARNet/accuracy/confusion_matrix之上追加两个自包含接口：

```
build_dataset_loaders(batch_size=8)      合成可分两类(3,32,32)，禁下载真实CIFAR10
train_and_validate(model, train, val)    完整训练+验证循环 → {train_loss,val_loss,val_acc}
```

TestMiniCapstone(4)：loader结构与形状 / 端到端报告合法性 /
可分任务6 epoch val_acc≥0.7 / 混淆矩阵与模型输出打通（元素和==样本数）。
注意：day20 answer.py自包含——评分环境只有当天文件，
毕业项目要求学生**独立重写**训练闭环而非import Day13。

### required_output字段

纯JSON内容层字段（Task dataclass/CLI未动，schema冻结保持）：

```json
Day13: ["一个可训练的CNN模型", "一次完整训练过程", "训练loss记录", "验证accuracy"]
Day20: ["合成Dataset与train/val两个DataLoader", "CNN在双loader上完成训练与验证",
        "accuracy与混淆矩阵评估报告"]
```

---

## 连续学习可行性确认（Day11→Day20）

| 日 | 主题 | 依赖上游 | 为下游提供 |
|----|------|---------|-----------|
| D11 | Tensor基础+环境体检 | NumPy/slicing | tensor/device/autograd心智模型 |
| D12 | Dataset/DataLoader | D11张量操作 | 批处理管线 |
| D13 | CNN完整训练闭环 | D12 loader | fit_classifier范式 |
| D14 | 正则化+Validation+loss curve | D13训练闭环 | 划分/评估/曲线判读 |
| D15 | 训练Debug | D11-D14全部故障面 | 四工具+分诊表 |
| D16 | TensorBoard | D14曲线概念 | 可视化输出 |
| D17 | checkpoint | D14保存直觉 | 断点续训 |
| D18 | 完整框架 | D13+D14+D17 | 标准训练器 |
| D19 | ResNet | D13结构+D14正则 | 深度架构 |
| D20 | **毕业小项目** | 全部 | Phase3入场券 |

依赖单调递增、无前向引用缺口；每一天的prerequisites均可在前序天完成。
**结论：Day11-Day20可以连续学习。**

## 回归状态

- pytest 762 passed / 343 skipped / 0 failed（本轮净增10个测试）
- 注册表83条，Task skills与test markers双向解析通过、无孤儿
- hint_levels升序、L1无代码约束全段合规
