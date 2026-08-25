# -*- coding: utf-8 -*-
"""讲义示意图生成（matplotlib，中文字体，运行时生成到临时目录后嵌入docx）"""
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

_DIAGRAM_DIR = None


def _out(name):
    global _DIAGRAM_DIR
    if _DIAGRAM_DIR is None:
        _DIAGRAM_DIR = Path(tempfile.mkdtemp(prefix="textbook_diagrams_"))
    return _DIAGRAM_DIR / name


def flow_diagram(title, steps, out_name, box_color="#eef4ff"):
    """竖向流程: 步骤框 + 向下箭头"""
    n = len(steps)
    fig, ax = plt.subplots(figsize=(4.2, 0.75 * n + 0.9))
    ax.axis("off")
    fig.suptitle(title, fontsize=13, fontweight="bold", y=0.97)
    top = 0.88
    height = 0.62 / max(n, 1)
    gap = 0.30 / max(n - 1, 1)
    for i, step in enumerate(steps):
        y = top - i * (height + gap)
        box = plt.Rectangle((0.15, y - height / 2), 0.7, height,
                            transform=fig.transFigure, facecolor=box_color,
                            edgecolor="#3b6ea5", linewidth=1.4, zorder=2)
        fig.patches.append(box)
        ax.text(0.5, 1 - (y / top), f"{i + 1}. {step}", transform=fig.transFigure,
                ha="center", va="center", fontsize=11)
    for i in range(n - 1):
        y = top - i * (height + gap) - height / 2 - gap / 2
        ax.annotate("", xy=(0.5, top - (i + 1) * (height + gap) + height / 2 + gap / 2),
                    xytext=(0.5, y), xycoords="figure fraction",
                    textcoords="figure fraction",
                    arrowprops=dict(arrowstyle="->", lw=1.6, color="#3b6ea5"))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    plt.savefig(_out(out_name), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return _out(out_name)


def curve_diagram(title, xs, ys, out_name, xlabel="迭代次数", ylabel="Loss"):
    """简单曲线(如loss下降)"""
    fig, ax = plt.subplots(figsize=(5, 2.8))
    ax.plot(xs, ys, marker="o", color="#c0504d", linewidth=1.6)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.35)
    plt.savefig(_out(out_name), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return _out(out_name)


def mlp_diagram(out_name):
    """MLP三层结构: 输入→隐层→输出"""
    fig, ax = plt.subplots(figsize=(5.6, 2.2))
    ax.axis("off")
    layers = [("输入层", 4, "#dbe5f1"), ("隐层 ReLU", 3, "#fde9d9"),
              ("输出层", 2, "#e2efda")]
    x_positions = [0.08, 0.5, 0.92]
    for (label, size, color), x in zip(layers, x_positions):
        for j in range(size):
            y = 0.5 + (j - (size - 1) / 2) * 0.16
            c = plt.Circle((x, y), 0.045, color=color, ec="#3b6ea5", lw=1.2)
            ax.add_patch(c)
        ax.text(x, -0.12, label, ha="center", fontsize=11)
    for xa, xb in zip(x_positions[:-1], x_positions[1:]):
        for ya in [0.18, 0.5, 0.82]:
            for yb in [0.34, 0.5, 0.66]:
                ax.plot([xa + 0.05, xb - 0.05], [ya, yb], color="#9db8d8",
                        lw=0.5, alpha=0.8)
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.25, 1)
    ax.set_title("多层感知机（MLP）结构", fontsize=12, fontweight="bold")
    plt.savefig(_out(out_name), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return _out(out_name)


def computation_graph(out_name):
    """Autograd计算图: x → ×a → + → ×x²… 简化为 y=a·x²+b·x+c 三支路"""
    fig, ax = plt.subplots(figsize=(5.8, 2.6))
    ax.axis("off")
    nodes = {
        "x": (0.08, 0.55), "mul_a": (0.30, 0.75), "sq": (0.30, 0.55),
        "mul_b": (0.30, 0.35), "mul_a2": (0.52, 0.75), "add1": (0.74, 0.55),
        "y": (0.94, 0.55),
    }
    labels = {"x": "x", "mul_a": "a·x", "sq": "x²", "mul_b": "b·x",
              "mul_a2": "a·x²", "add1": "a·x²+b·x", "y": "y=…+c"}
    for name, (px, py) in nodes.items():
        c = plt.Circle((px, py), 0.055, facecolor="#eef4ff", ec="#3b6ea5", lw=1.3)
        ax.add_patch(c)
        ax.text(px, py, labels[name], ha="center", va="center", fontsize=9.5)
    edges = [("x", "mul_a"), ("x", "sq"), ("x", "mul_b"),
             ("mul_a", "mul_a2"), ("sq", "mul_a2"), ("mul_b", "add1"),
             ("mul_a2", "add1"), ("add1", "y")]
    for a, b in edges:
        (x1, y1), (x2, y2) = nodes[a], nodes[b]
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", lw=1.2, color="#5b7da0"))
    ax.text(0.5, 0.08, "backward(): 从 y 沿箭头反推每个节点的梯度",
            ha="center", fontsize=10.5, color="#7f3f00")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title("计算图与反向传播", fontsize=12, fontweight="bold")
    plt.savefig(_out(out_name), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return _out(out_name)
