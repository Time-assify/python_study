# 打包桌面应用（PythonStudy.exe）

使用 PyInstaller 将 GUI 打包为 Windows 单文件可执行程序。
打包必须在 **Windows** 上进行（生成 .exe）；macOS/Linux 同理各自平台执行。

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

## 2. PyInstaller 打包命令（Windows cmd/PowerShell）

```bash
pyinstaller --noconfirm --onefile --windowed ^
  --name PythonStudy ^
  --add-data "tasks;tasks" ^
  --add-data "config;config" ^
  --add-data "configs;configs" ^
  --hidden-import pytest_jsonreport ^
  run_app.py
```

说明：
- `--add-data` 在Windows用分号`;`分隔源与目标；课程数据(tasks/)、
  知识点注册表(config/)、平台配置(configs/)必须随包携带。
- `--windowed` 隐藏控制台；调试期可去掉以查看traceback。
- pytest相关插件由平台在评测子进程中动态探测，
  PyInstaller无法静态发现，故用`--hidden-import`显式声明；
  若运行时报缺失插件，按同样方式追加。

## 3. 产物结构

```
dist/
  PythonStudy.exe      ← 双击即用
build/                 ← 中间产物可删除
PythonStudy.spec       ← 可版本化; 后续可直接 pyinstaller PythonStudy.spec
```

> 注意：`dist/PythonStudy.exe` 启动后会在exe所在目录读写数据库文件。
> 建议把 exe 放到一个有写权限的独立目录再运行。

## 4. 数据库与用户数据

学习数据(SQLite)默认落在工作目录。升级exe时保留同目录下的
`learning.db`（或按首次启动提示迁移），即可延续学习进度。

## 5. 常见问题

| 现象 | 处理 |
|------|------|
| 双击无反应 | 去掉`--windowed`重新打包，看控制台报错 |
| 提示找不到 tasks/dayXX.json | `--add-data`漏了对应目录 |
| 评测时pytest插件报错 | 补对应`--hidden-import` |
| 杀软误报 | PyInstaller onefile常见误报，加白名单或改用`--onedir` |
