# -*- coding: utf-8 -*-
"""SkillMapper: 测试失败 -> skill -> KnowledgeGapRecord (P0-1)

通过AST解析 tests/dayXX_test.py 中类级 @pytest.mark.skill(...) 标记，
建立 {测试函数名: [skills]} 索引；失败时自动映射并生成
KnowledgeGapRecord(skill, knowledge_point={id,name}, count)。

不修改Evaluator架构——只读取其产出的失败测试名列表。
"""
import ast
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

from ..models import KnowledgeGapRecord

# skill id -> 中文知识点名（用于knowledge_point.name）
SKILL_LABELS = {
    "python.project_structure": "项目结构组织",
    "python.logging": "日志模块",
    "python.decorator": "装饰器",
    "python.generator": "生成器",
    "python.context_manager": "上下文管理器",
    "python.abc": "抽象基类",
    "python.oop": "面向对象",
    "python.threading": "多线程",
    "python.multiprocessing": "多进程",
    "python.requests": "HTTP请求",
    "numpy": "NumPy数组",
    "pandas": "Pandas数据处理",
    "ml.linear_regression": "线性回归",
    "ml.loss": "损失函数",
    "pytorch.tensor": "Tensor基础",
    "pytorch.autograd": "自动求导",
    "pytorch.nn_module": "nn.Module",
    "pytorch.activation": "激活函数",
    "pytorch.dataset": "Dataset",
    "pytorch.dataloader": "DataLoader",
    "pytorch.optimizer": "优化器",
    "pytorch.lr_scheduler": "学习率调度",
    "pytorch.cnn": "卷积神经网络",
    "pytorch.batchnorm": "批归一化",
    "pytorch.dropout": "Dropout",
    "pytorch.device": "设备管理",
    "pytorch.training_step": "训练单步",
    "pytorch.tensorboard": "TensorBoard",
    "pytorch.checkpoint": "模型检查点",
    "pytorch.training_loop": "训练循环",
    "pytorch.resnet": "残差网络",
    "evaluation.accuracy": "准确率评估",
    "metrics.confusion_matrix": "混淆矩阵",
    "cv.augmentation": "数据增强",
    "cv.classification": "图像分类",
    "transfer_learning": "迁移学习",
    "parameter_freezing": "参数冻结",
    "nlp.tokenization": "分词",
    "nlp.embedding": "词嵌入",
    "transformer.attention": "注意力机制",
    "transformer.positional_encoding": "位置编码",
    "huggingface.model": "HuggingFace模型",
    "detection.anchor": "锚框",
    "detection.iou": "IoU",
    "detection.nms": "非极大值抑制",
    "detection.dataset": "检测数据集",
    "metrics.average_precision": "AP指标",
    "deployment.onnx": "ONNX导出",
    "deployment.fastapi": "FastAPI服务",
    "engineering.config": "配置管理",
    "application.pipeline": "应用流水线",
    "llm.client": "LLM客户端",
    "llm.streaming": "流式输出",
    "llm.retry": "重试机制",
    "llm.json_parsing": "JSON解析",
    "prompt.few_shot": "少样本提示",
    "prompt.chain_of_thought": "思维链",
    "rag.chunking": "文档分块",
    "rag.retrieval": "向量检索",
    "text.chunking": "文本分块",
    "agent.tool_calling": "工具调用",
    "agent.tool": "Agent工具",
    "agent.memory": "Agent记忆",
    "agent.schema_validation": "Schema校验",
    "codegen.generation": "代码生成",
    "codegen.review": "代码审查",
    "grading.scoring": "评分系统",
    "engineering.sandbox": "沙箱执行",
    "recommendation": "推荐逻辑",
    "learning.profile": "学习画像",
    "system.pipeline": "系统流水线",
    "system.retry": "系统重试",
    "system.event_bus": "事件总线",
    "system.health_check": "健康检查",
    "capstone.platform": "综合平台",
    "documentation": "文档编写",
    "api.client": "API客户端",
    "api.server": "API服务端",
    "data.cleaning": "数据清洗",
    "pytorch.tensor_shape": "Tensor维度",
}

_NODEID_TAIL = re.compile(r"([\w]+)::(?:[\w]+::)*([A-Za-z_][A-Za-z0-9_]*)\s*$")


def _extract_test_name(raw: str) -> str:
    """从nodeid或裸函数名中提取测试函数名

    'tests/day02_test.py::TestDecorators::test_repeat_executes_n_times'
      -> 'test_repeat_executes_n_times'
    """
    m = _NODEID_TAIL.search(raw)
    return m.group(2) if m else raw.strip()


class SkillMapper:
    """day级 {测试函数名: skills} 索引与失败映射"""

    def __init__(self, tests_dir: Optional[Path] = None):
        self.tests_dir = Path(tests_dir) if tests_dir else Path(__file__).parent.parent.parent / "tests"
        self._index_cache: Dict[int, Dict[str, List[str]]] = {}

    def build_index(self, day: int) -> Dict[str, List[str]]:
        """AST解析 day{day}_test.py，返回 {测试函数名: [skill,...]}（带缓存）"""
        if day in self._index_cache:
            return self._index_cache[day]
        path = self.tests_dir / f"day{day:02d}_test.py"
        index: Dict[str, List[str]] = {}
        if path.exists():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_skills = self._skills_from_decorator(node)
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                                and item.name.startswith("test_"):
                            # 类内方法继承类标记；方法自带标记则合并
                            own = self._skills_from_decorator(item)
                            merged = list(dict.fromkeys(class_skills + own))
                            if merged:
                                index[item.name] = merged
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                        and node.name.startswith("test_"):
                    own = self._skills_from_decorator(node)
                    if own:
                        index[node.name] = own
        self._index_cache[day] = index
        return index

    @staticmethod
    def _skills_from_decorator(node) -> List[str]:
        skills: List[str] = []
        for dec in node.decorator_list:
            call = dec.func if isinstance(dec, ast.Call) else dec
            if isinstance(call, ast.Attribute) and call.attr == "skill":
                args = dec.args if isinstance(dec, ast.Call) else []
            elif isinstance(call, ast.Name) and call.id == "skill":
                args = dec.args if isinstance(dec, ast.Call) else []
            else:
                continue
            for arg in args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    skills.append(arg.value)
        return skills

    def map_failures(self, day: int, failed_test_names: List[str]) -> Dict[str, int]:
        """失败测试名 -> {skill: 失败次数}"""
        index = self.build_index(day)
        counter: Counter = Counter()
        for raw in failed_test_names:
            name = _extract_test_name(raw)
            for skill in index.get(name, []):
                counter[skill] += 1
        return dict(counter)

    def build_records(self, day: int, failed_test_names: List[str]) -> List[KnowledgeGapRecord]:
        """失败测试 -> KnowledgeGapRecord列表（按skill聚合计数）"""
        records = []
        for skill, count in sorted(self.map_failures(day, failed_test_names).items()):
            label = SKILL_LABELS.get(skill, skill)
            records.append(KnowledgeGapRecord(
                skill=skill,
                knowledge_point={"id": skill, "name": label},
                count=count,
            ))
        return records
