# 打包桌面应用（PythonStudy.exe）

使用 PyInstaller 将 GUI 打包为 Windows 可执行程序。
打包必须在 **Windows** 上进行；macOS/Linux 同理各自平台执行。

> 推荐模式：`--onedir`。产物是一个文件夹，双击其中的 `PythonStudy.exe`
> 即可启动；数据库与配置都在文件夹内，天然可持久化、可整体拷贝迁移。

## 0. 准备

```bash
pip install -r requirements.txt          # 平台基础依赖
pip install -r requirements-pytorch.txt  # 进入PyTorch天后需要(体积大, 按需)
pip install -r requirements-app.txt      # PySide6
pip install pyinstaller
```

## 1. 先本地验证GUI可启动

```bash
python run_app.py --check    # 输出 OK: MainWindow built with 4 pages
python run_app.py            # 真窗口冒烟
```

## 2. 实测通过的打包命令（Windows）

```bash
pyinstaller --noconfirm --onedir --windowed ^
  --name PythonStudy ^
  --add-data "tasks;tasks" ^
  --add-data "config;config" ^
  --add-data "configs;configs" ^
  --hidden-import pytest_jsonreport ^
  --exclude-module torch --exclude-module torchvision ^
  --exclude-module transformers --exclude-module faiss ^
  --exclude-module faiss_cpu --exclude-module sklearn ^
  --exclude-module scipy --exclude-module nltk ^
  --exclude-module tokenizers --exclude-module safetensors ^
  run_app.py
```

实测数据（本仓库）：构建约2分钟；产物 **224 MB**；
未加排除项时会被静态分析拖入 torch/transformers/faiss 等，
膨胀到 **842 MB**——GUI启动并不需要它们，务必保留排除清单。

要点：
- `--add-data` 在Windows用分号`;`分隔源与目标；课程(tasks/)、
  知识点注册表(config/)、平台配置(configs/)必须随包携带。
- `run_app.py` 已内置冻结态引导：启动时自动 `chdir` 到解包目录，
  因此双击exe后课程/注册表/SQLite都能正确定位与持久化。
- `--windowed` 隐藏控制台；调试期去掉它可看traceback。

## 3. 产物与使用

```
dist/
  PythonStudy/
    PythonStudy.exe     ← 双击即用
    _internal/          ← 运行库+资源(勿单独移动)
build/                  ← 中间产物可删除
PythonStudy.spec        ← 可版本化; 之后直接 pyinstaller PythonStudy.spec
```

把整个 `PythonStudy` 文件夹拷给使用者 → 双击 `PythonStudy.exe`。
想要"桌面单击"：右键exe → 发送到桌面快捷方式。

## 4. 已知边界（重要）

| 能力 | exe内状态 | 说明 |
|------|----------|------|
| 浏览40天任务/Hint分级/Dashboard/学习记录 | ✅ 完整可用 | 纯读取本地资源 |
| 提交代码评测(pytest子进程) | ⚠ 受限 | 冻结环境下`sys.executable`指向exe本身, pytest子进程链路不可靠 |

因此**完整学习闭环推荐源码方式运行**：

```bash
pip install -r requirements.txt -r requirements-app.txt
python run_app.py
```

GUI在检测到打包环境时会在提交页顶部显示上述提示（app/pages/submit_page.py）。
后续若要打通exe内完整评测，需引入随包便携Python或改造Evaluator的
子进程构造方式——两者都超出当前"不改平台核心"约束，留待v2评估。

## 5. 常见问题

| 现象 | 处理 |
|------|------|
| 双击无反应 | 去掉`--windowed`重新打包，看控制台报错 |
| 提示找不到 tasks/dayXX.json | `--add-data`漏了对应目录 |
| 杀软误报 | PyInstaller常见误报，加白名单 |
| 想要单文件exe | 改`--onefile`（首次启动解包变慢，且DB落在临时目录不利存档，不推荐） |
