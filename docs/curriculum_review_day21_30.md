# Day21-Day30 课程审核：Computer Vision项目路径（Round 2/4）

> 基线：caa5361。目标路径：**PyTorch基础 → 计算机视觉能力 → 完整CV项目**。
> 平台/Evaluator/Database/AI Agent/Task Schema零改动。
> 变更范围：任务JSON内容、测试文件、知识点注册表内容项、依赖清单。

## 总体检查原则执行情况

| 原则 | 结论 |
|------|------|
| core_task ≤90min，挑战另计30-60min | D23重定位为90；D18/19/20/30等120分钟日均已把重活放挑战位（核心≈90语义成立），挑战文本标注进阶耗时 |
| 禁止单日捆绑数据集+模型+训练+调参+部署 | D26(概念)/D27(数据与指标)/D28(导出)已天然拆分；D30综合项目为组装考核而非新知识 |
| 数据集难度 | 全段0处真实下载引用（扫描实证）；全部合成张量/数组 |

## 逐日审核

# Day21

## Goal

图像张量表示 + 数据增强。

## Prerequisites

CNN训练闭环（D13）、验证评估（D14）。

## Estimated Time

120分钟（核心约90）。

## Risk

原契约只有增强管线，缺失"图片三形态"认知——HWC→CHW→Tensor是CV第一道坎，
此前完全依赖学生自行领悟。

## Modification

【已应用】required_api追加`image_to_tensor(img_hwc)`（HWC 0-255 → CHW float[0,1]，
通道序不得置换）；TestImageTensor(2)锁shape/dtype/range/通道序；
skills增`cv.image_tensor`/`cv.transform`（注册表同步新增）；mastery补转换说明能力。

# Day22

## Goal

迁移学习流程。

## Prerequisites

CNN训练闭环、state_dict与参数遍历。【已应用：原为空】

## Estimated Time

120分钟（核心约90）。

## Risk

初学者直接上手大型预训练模型微调——P0-3明确要求闸门。

## Modification

【已应用】core_task/mastery显式闸门措辞："核心=理解冻结-特征提取-按需解冻流程；
大型预训练模型完整微调实操放挑战"。测试保持小型自建backbone（无需下载权重）。

# Day23

## Goal

图像分类数据集与训练闭环（**主题重写**：原NLP基础）。

## Prerequisites

CNN训练闭环、正则化与验证、checkpoint概念。

## Estimated Time

90分钟。【已应用：120→90——四接口聚焦日，契合"上班族晚上1小时"】

## Risk

原NLP分词日阻断CV主线（P0-1要求D21-23形成基础CV能力）；
且分类任务缺"模型保存文件"产物（P0-2三件套之一）。

## Modification

【已应用】整日重写为CV：
- `make_color_samples`合成可分两类HWC彩色图（无下载）
- `ImagesDataset`完成HWC→CHW归一化封装
- `cnn_baseline`(16x16小卷积) + `train_classifier`(双循环+最优权重落盘)
- TestImagesDataset(2)+TestTrainClassifier(4)，含**保存权重→新模型复现val_acc**
  的闭环断言与可分任务val_acc≥0.9学习断言
- required_output=["训练loss","validation accuracy","模型保存文件"]（P0-2原文）
- nlp.tokenization/nlp.embedding从注册表移除（唯一归属即本日，随主题退役；
  tokenization按需在Phase4 LLM段重引入）

# Day24

## Goal

Transformer核心组件（自注意力/多头/位置编码）。

## Prerequisites

线性层与softmax、序列数据概念。【已应用：原为空】

## Estimated Time

120分钟（核心约90）。

## Risk

定位说明不足——易被误解为CV主线必经点。

## Modification

【已应用】仅元数据补齐。定位声明：D24-D25是**序列建模桥梁**，
为Phase4 LLM段供能；CV主线不依赖此日（见文末连续性表）。
纯张量数学实现，无tokenizer依赖 ✓。

# Day25

## Goal

HuggingFace结构离线操作。

## Prerequisites

attention机制、padding与mask概念。【已应用：原为空】

## Estimated Time

120分钟。

## Risk

HF生态默认在线下载——与上班族CPU环境冲突。

## Modification

【已应用】元数据补齐。已有设计合规：测试头明示"离线构建，不下载权重"。
nlp.tokenization未挂靠本日（pad_ids属编码后处理）——避免复活孤儿。

# Day26

## Goal

检测基础概念：锚框/IoU/NMS。

## Prerequisites

边界框编码[x1,y1,x2,y2]、滑窗与网格概念。【已应用：原为空】

## Estimated Time

120分钟（核心约90）。

## Risk

P1-3要求detection前掌握bbox/IoU/NMS——本日即概念日，顺序天然正确 ✓。
但precision/recall此前无任何覆盖。

## Modification

【已应用】mastery追加两条理解性要求：IoU阈值对匹配/NMS的影响、
precision/recall含义（P1-1：重点理解，不要求手写）。

# Day27

## Goal

检测数据集与AP指标实战。

## Prerequisites

bbox/IoU/NMS(D26)、AP指标定义。【已应用：原为空】

## Estimated Time

120分钟。

## Risk

AP实现复杂度容易失控。

## Modification

【已应用】prerequisites显式声明D26前置链（P1-3拆分确认：
基础检测概念(D26) → 检测pipeline(D27)）；mastery补PR曲线直觉。
合成检测数据 ✓ CPU可完成 ✓。

# Day28

## Goal

ONNX导出与跨运行时推理。

## Prerequisites

CNN模型结构、推理与训练模式差异。【已应用：原为空】

## Estimated Time

120分钟。

## Risk

torch.onnx.export依赖onnx/onnxruntime包，而requirements-pytorch.txt
只声明了torch/torchvision/tensorboard——真实评分环境ImportError
（同Day16 tensorboard问题模式）。

## Modification

【已应用】requirements-pytorch.txt追加onnx>=1.14 / onnxruntime>=1.16。
部署单列一日 ✓ 不与训练/调参捆绑。

# Day29

## Goal

FastAPI服务部署。

## Prerequisites

模型推理调用、HTTP请求响应基础。【已应用：原为空】

## Estimated Time

120分钟。

## Risk

网络依赖错觉。

## Modification

【已应用】元数据补齐。fastapi/httpx已在base依赖 ✓ 测试走TestClient无网络 ✓。

# Day30

## Goal

**CV阶段综合项目**（主题重写：原AI应用整合）。

## Prerequisites

CNN训练闭环、checkpoint保存恢复、yaml配置读写。

## Estimated Time

120分钟（核心约90 + 进阶挑战30）。

## Risk

原config/pipeline/monitor通用工程日与CV路径无关，Phase3收官没有
完整项目承载点——P1-4明确要求Day30结束完成小项目。

## Modification

【已应用】整日重写为毕业项目（五阶段：数据→模型→训练→评价→结果展示）：
- `TrainConfig`(dataclass+yaml roundtrip)——保留配置驱动基因(engineering.config)
- `make_loaders`合成可分两类(3,32,32)，禁下载
- `build_model` + `run_pipeline(config)`→{train_loss,val_loss,val_acc,model_path}，
  val_loss创新低即落盘最优权重(application.pipeline技能保留并重新赋义)
- TestTrainConfig(3)+TestRunPipeline(4)，含**加载产物权重复现报告acc**
  （结果可展示的底线断言）
- required_output=["yaml训练配置文件","训练loss与validation accuracy报告",
  "最优权重文件(model_path)"]
- application.pipeline/engineering.config双技能保号，零注册表孤儿

---

## P0/P1 覆盖矩阵

| 审核项 | 状态 |
|--------|------|
| P0-1 D21-23基础CV(HWC→CHW/Dataset/Transform/Augmentation) | D21 image_to_tensor+三形态 / D22流程闸门 / D23 Dataset+闭环 ✓；knowledge_points新增cv.image_tensor/cv.transform(cv.augmentation已存在) |
| P0-2 分类完整性+required_output | D23/D20均含Dataset→…→Metric全链；required_output三件套精确落地 |
| P0-3 复杂度闸门 | ResNet=D19(前段)；TL=D22闸门措辞；ViT/YOLO大模型实操不存在于核心 |
| P1-1 CV指标 | 分类acc/cm(D20)+验证acc(D14/23/30)；检测IoU(D26)+AP(D27)+PR理解(mastery)；不强制全手写 |
| P1-2 数据集难度 | 全段0下载引用（正则扫描实证）；合成数据全覆盖 |
| P1-3 检测前置链 | D26概念日→D27 pipeline日，顺序即拆分 ✓ |
| P1-4 阶段综合项目 | D30毕业项目五阶段+三产物+可复现断言 |

## 注册表变更

- 新增：cv.image_tensor(图像张量表示,cv,2) / cv.transform(图像变换管线,cv,3)
- 移除：nlp.tokenization / nlp.embedding（唯一归属day23随主题退役）
- 终态83条，双向解析+无孤儿校验通过

## 连续学习结论

PyTorch基础(D11-15) → 可视化/存取/框架(D16-18) → 深度架构与分类实战(D19-20)
→ **图像表示与增强(D21) → 迁移学习(D22) → CV分类闭环(D23)** → 序列建模桥梁(D24-25,
Phase4供能支线) → **检测概念(D26) → 检测指标实战(D27) → 导出(D28) → 服务(D29)
→ CV毕业项目(D30)**。主线无断裂，支线定位清晰。**Day21-Day30可以连续学习。**
