# -*- coding: utf-8 -*-
"""Part 1 内容：Day01-Day10 Python工程基础（纯教学讲义）"""
from . import diagrams as dg

PART1 = {
    "title": "第一部分  Python 工程基础（Day01–Day10）",
    "intro": ("本部分把Python从零基础讲到能支撑机器学习工程。十天内你将获得三样东西："
              "规范化的工程习惯、Python进阶特性（装饰器/生成器/OOP/并发/网络），以及"
              "第一段真正属于自己的机器学习代码——手写梯度下降的线性回归。"
              "从Day08开始Tensor/Autograd/nn.Module为第二部分PyTorch铺路。"),
    "days": [
# ------------------------------------------------------------------ Day01
{
    "day": 1,
    "title": "Python项目结构与工程规范",
    "goal": "学完今天，你能够从零创建一个结构规范的机器学习项目目录，会用YAML管理配置，并给程序配上文件日志——这是所有后续40天的容器。",
    "why": [
        "真实项目不是单个脚本：代码、测试、配置、数据、日志混在一起，两周后连作者自己都找不到东西。工业界用**约定俗成的目录结构**解决这个问题。",
        "把参数写死在代码里，每次换数据路径都要改代码再运行；把配置放进独立文件，**改配置不改代码**，还方便别人复现实验。",
        "程序跑挂了、深夜训练崩了，没有日志就只能靠猜。**logging把问题现场固化下来**，是工程师的第一根救命稻草。",
    ],
    "core": [
        ("目录约定", [
            "root/ 下分 src（源码）、tests（测试）、configs（配置）、data（数据）、logs（日志）五个子目录，职责单一。",
            "src 里的 __init__.py 把一个目录标记为Python包，让 from src.xxx import yyy 成为可能。",
        ]),
        ("配置与日志", [
            "- **YAML** 是“人类可读的JSON”：键值对+缩进，天然适合放实验参数。",
            "- logging三要素：Logger（记录器）、Handler（输出到哪里，如文件）、Level（INFO/WARNING/ERROR按严重程度过滤）。",
            "- logger.info(...) 写入文件而不是 print(...)——print在工程代码里是被禁止的调试手段。",
        ]),
    ],
    "diagrams": [
        ("ascii", (
            "ml_project/            ← 项目根目录\n"
            "├── src/                ← 源码（含 __init__.py 才是包）\n"
            "│   └── model.py\n"
            "├── tests/              ← 测试代码（每个功能都有测试）\n"
            "├── configs/            ← YAML配置文件\n"
            "├── data/               ← 数据集（大文件不进git）\n"
            "└── logs/               ← 程序运行日志\n"),
         "规范的机器学习项目目录"),
    ],
    "code": [
        ("创建一个包结构的最小实现", (
            "import os\n"
            "def create_project_structure(project_name):\n"
            "    dirs = {}\n"
            "    for sub in ('src', 'tests', 'configs', 'data', 'logs'):\n"
            "        path = os.path.join(project_name, sub)\n"
            "        os.makedirs(path, exist_ok=True)   # 存在也不报错\n"
            "        dirs[sub] = path\n"
            "    # src是包：放一个空的__init__.py\n"
            "    open(os.path.join(dirs['src'], '__init__.py'), 'w').close()\n"
            "    return dirs\n"),
         ["os.makedirs(..., exist_ok=True)：exist_ok=True让重复调用不再抛异常——工程里几乎总是打开它。",
          "open(...).close() 创建一个空文件；__init__.py 内容不重要，存在本身就是标志。",
          "返回目录字典，调用方可以继续往里放东西，而不是去猜路径。"]),
        ("给程序加文件日志", (
            "import logging\n"
            "def setup_logger(log_file, level=logging.INFO):\n"
            "    logger = logging.getLogger('ml_project')\n"
            "    logger.setLevel(level)\n"
            "    handler = logging.FileHandler(log_file)   # 写到文件\n"
            "    logger.addHandler(handler)\n"
            "    return logger\n"
            "\n"
            "log = setup_logger('logs/train.log')\n"
            "log.info('训练开始: lr=0.01')   # 这行会落盘，程序挂了也能看到\n"),
         ["getLogger('名字')：同一个名字全局共享同一个记录器，避免各模块各自为政。",
          "FileHandler把输出定向到文件；想同时看屏幕再加一个StreamHandler。",
          "info/warning/error是给“别人”看的信息，不是给自己调试的临时print。"]),
    ],
    "practice": [
        "- **配置外置**：超参数、路径一律进configs/的YAML，代码只读配置。",
        "- **日志分级**：开发期DEBUG，日常INFO，异常ERROR——上线后按级别过滤。",
        "- **可复制性**：目录+配置+日志三件套，是“别人能复现你结果”的最低门槛。",
    ],
    "mistakes": [
        {"q": "路径写死 E:\\data\\train.csv，换机器就崩", "reason": "把环境信息混进代码", "fix": "路径进配置文件或由参数传入"},
        {"q": "同一个logger重复addHandler，日志每条打印两遍", "reason": "每次调用都新建Handler", "fix": "用getLogger单例，或先检查是否已有Handler"},
        {"q": "os.makedirs重复运行抛 FileExistsError", "reason": "没开exist_ok", "fix": "恒用 exist_ok=True"},
    ],
    "summary": {
        "learned": ["五目录工程结构及职责", "__init__.py与包的概念", "YAML配置的读写思想", "logging三要素"],
        "must": ["不看任何资料，手写出目录创建函数", "解释为什么print不能替代日志"],
    },
    "task_link": "今天任务对应 tasks/day01.json：三个接口（create_project_structure / create_config_file / setup_logger）正是上面三块知识的最小落地。任务只要求“能创建+能落盘”，但你要意识到它是在给未来40天搭地基。",
},
# ------------------------------------------------------------------ Day02
{
    "day": 2,
    "title": "装饰器、生成器与上下文管理器",
    "goal": "学完今天，你能够把“重复的逻辑”抽成装饰器复用（如缓存、计时、重试），用生成器处理放不进内存的大数据，并用with安全地管理资源。",
    "why": [
        "缓存函数结果、记录函数耗时、权限检查——这些**横切逻辑**如果复制粘贴进每个函数，改一处要改十处；装饰器让它们只写一次。",
        "一个1GB的文件一次性读进内存就爆了；生成器让数据**用多少取多少（惰性求值）**，内存占用恒定。",
        "文件、网络连接、计时器都有“用完必须释放/收尾”的宿命，with语句保证**无论正常还是异常都执行清理**。",
    ],
    "core": [
        ("装饰器", [
            "- 函数是**一等公民**：可以当参数传、当返回值。",
            "- 装饰器=接收函数、返回新函数的函数；@语法糖只是调用的简写。",
            "- **functools.wraps**把原函数的名字、文档透传到包装函数——没有它，调试时看到的都是wrapper。",
        ]),
        ("生成器", [
            "- 含 **yield** 的函数是生成器函数：调用它不执行函数体，而是返回生成器对象。",
            "- 每次next()执行到下一个yield并**暂停**，状态保留——这就是惰性。",
            "- 适合：大数据流式处理、无限序列（如斐波那契）。",
        ]),
        ("上下文管理器", [
            "- with 背后调用 __enter__/__exit__；__exit__ 在异常时也会执行。",
            "- 典型用途：计时器（进入记时间，退出算耗时）、文件、锁。",
        ]),
    ],
    "diagrams": [
        ("image", lambda: dg.flow_diagram(
            "装饰器 @repeat(3) 的执行流程",
            ["调用被装饰的 work()", "进入wrapper：循环 i=1..3", "执行原函数 work()",
             "记录最后一次返回值", "wrapper返回最终结果"], "day02_decorator.png"),
         "装饰器=在函数外面包一层循环"),
    ],
    "code": [
        ("用装饰器实现函数结果缓存（memoize）", (
            "from functools import wraps\n"
            "def memoize(func):\n"
            "    cache = {}\n"
            "    @wraps(func)                      # 保留原函数信息\n"
            "    def wrapper(*args):\n"
            "        if args not in cache:         # 命中缓存直接返回\n"
            "            cache[args] = func(*args)\n"
            "        return cache[args]\n"
            "    return wrapper\n"
            "\n"
            "@memoize\n"
            "def slow_add(a, b):\n"
            "    return a + b                     # 假装很慢\n"),
         ["cache字典活在wrapper闭包里，跨调用共享——装饰器的“记忆”。",
          "@wraps(func)一行换来函数名/文档不丢失，调试体验完全不同。",
          "注意缓存键是args元组；参数必须可哈希（列表不行）。"]),
        ("生成器：斐波那契只产n个", (
            "def fibonacci(n):\n"
            "    a, b = 0, 1\n"
            "    for _ in range(n):\n"
            "        yield a          # 产出一个就暂停\n"
            "        a, b = b, a + b\n"
            "\n"
            "for x in fibonacci(5):\n"
            "    print(x)              # 0 1 1 2 3\n"),
         ["yield a：交出a并把执行停在原地，下次for继续从这里往下走。",
          "n=0时循环不执行，生成器为空——天然符合直觉。",
          "对比：返回整个列表要一次算完n项；生成器算一项交一项。"]),
    ],
    "practice": [
        "- **缓存IO**：对数据库查询/网络请求包memoize，收益立竿见影。",
        "- **流式管道**：读文件→逐行yield→逐行处理，恒定内存。",
        "- **计时与资源**：Timer/文件都交给with，把“收尾”从业务代码里拿走。",
    ],
    "mistakes": [
        {"q": "装饰器返回了f(*args)而不是wrapper", "reason": "装饰器是“返回新函数”的函数，返回调用结果等于没装饰", "fix": "装饰器函数体内定义wrapper并return wrapper"},
        {"q": "被装饰函数的名字变成了wrapper", "reason": "没加@wraps", "fix": "在wrapper上加@wraps(func)"},
        {"q": "想复用生成器结果，list(gen)之后再for发现空了", "reason": "生成器只能消费一次", "fix": "需要重复访问就转成list保存，或重新创建生成器"},
    ],
    "summary": {
        "learned": ["装饰器=函数包装函数", "wraps的作用", "yield与惰性求值", "with与__enter__/__exit__"],
        "must": ["徒手写出memoize", "说出生成器与列表的本质区别"],
    },
    "task_link": "对应 tasks/day02.json：repeat/memoize/fibonacci/chunked/Timer。Timer是低门槛版上下文管理器——会写__enter__/__exit__即可，不做精确benchmark。这套“包装、惰性、资源管理”三件套会在Day31的LLM客户端（重试/流式）再次登场。",
},
# ------------------------------------------------------------------ Day03
{
    "day": 3,
    "title": "面向对象与抽象基类",
    "goal": "学完今天，你能够用抽象基类（ABC）定义“接口契约”，让不同实现可以无缝替换——这是框架设计和机器学习库的通用语言。",
    "why": [
        "一个训练系统要支持线性模型、决策树、神经网络；上层代码若为每种模型写一遍训练逻辑就爆炸了。**统一接口**让上层只认fit/predict两个方法。",
        "抽象基类=**契约**：声明“继承我的人必须实现这些方法”，没实现就禁止实例化，把错误提前到写代码时暴露。",
        "换模型不动上层——这就是**多态**：同一个调用，不同子类不同行为。",
    ],
    "core": [
        ("类与继承", [
            "- 类=数据(属性)+行为(方法)的封装；子类继承父类，可覆写方法。",
            "- **isinstance/issubclass** 判断类型关系。",
        ]),
        ("抽象基类ABC", [
            "- from abc import ABC, abstractmethod。",
            "- 被 @abstractmethod 修饰的方法**没有实现体**，子类必须实现。",
            "- 含抽象方法的类不能实例化——Python会直接报TypeError。",
        ]),
        ("多态", [
            "- 统一接口 + 各自实现：调用方写 model.fit(X, y)，不关心model到底是什么。",
            "- 这是sklearn、PyTorch里nn.Module等一切框架的组织方式。",
        ]),
    ],
    "diagrams": [
        ("ascii", (
            "BaseModel (ABC)          ← 契约: fit(X,y) / predict(X)\n"
            "      │\n"
            "      ├── LinearModel      ← 实现1: 线性公式\n"
            "      ├── TreeModel        ← 实现2: 决策树(将来)\n"
            "      └── NeuralModel      ← 实现3: 神经网络(将来)\n"
            "\n"
            "上层只调用 fit/predict —— 换子类，上层零改动（多态）\n"),
         "抽象基类定义契约，子类各显神通"),
    ],
    "code": [
        ("抽象基类与第一个实现", (
            "from abc import ABC, abstractmethod\n"
            "\n"
            "class BaseModel(ABC):\n"
            "    @abstractmethod\n"
            "    def fit(self, X, y):\n"
            "        \"\"\"用数据训练模型\"\"\"\n"
            "        ...\n"
            "\n"
            "    @abstractmethod\n"
            "    def predict(self, X):\n"
            "        \"\"\"对输入做预测\"\"\"\n"
            "        ...\n"
            "\n"
            "class LinearModel(BaseModel):\n"
            "    def fit(self, X, y):\n"
            "        self.w = 2.0        # 演示用: 记住一个规则\n"
            "    def predict(self, X):\n"
            "        return [self.w * x for x in X]\n"
            "\n"
            "# BaseModel()          ← 报错! 抽象类不能实例化\n"
            "# LinearModel()        ← OK, 实现了全部抽象方法\n"),
         ["抽象方法的函数体只写文档字符串和...，表示“这里不实现”。",
          "子类少实现任何一个抽象方法，实例化立刻TypeError——契约被强制执行。",
          "predict返回列表只是演示；Day07你会见到真正的模型。"]),
    ],
    "practice": [
        "- **插件式设计**：定义Base扩展点，团队各自实现，框架统一调度。",
        "- **测试用假实现**：单测时用FakeModel替换真实模型，无需真实数据。",
        "- **接口先行**：新系统先定ABC再写实现，能防止后期返工。",
    ],
    "mistakes": [
        {"q": "子类忘了实现某个抽象方法，运行到半路才崩", "reason": "没意识到抽象方法会被强制检查", "fix": "实例化子类时Python会报TypeError，把检查点提前利用起来"},
        {"q": "每个子类都复制一遍相同的预处理代码", "reason": "没把公共逻辑放父类", "fix": "公共代码写在父类普通方法里，子类只覆写差异部分"},
        {"q": "以为ABC只能空壳", "reason": "对抽象基类理解片面", "fix": "ABC可以有普通方法甚至属性，抽象方法才强制实现"},
    ],
    "summary": {
        "learned": ["类/继承/覆写", "abstractmethod的契约机制", "多态的意义"],
        "must": ["声明一个含两个抽象方法的ABC", "解释为什么BaseModel()会报错"],
    },
    "task_link": "对应 tasks/day03.json：BaseModel/LinearModel/OptimizerBase。任务很“小”，但它教会你的接口思维在Day10的nn.Module、Day34的Agent工具接口里会以更大规模重现。",
},
# ------------------------------------------------------------------ Day04
{
    "day": 4,
    "title": "多线程与ThreadPoolExecutor",
    "goal": "学完今天，你能够用线程池并行执行多个IO型任务，并清楚地区分“线程适合IO密集、进程适合CPU密集”。",
    "why": [
        "下载100个文件，顺序做完要100秒，并行可能只要5秒——瓶颈不是CPU而是**等待**。",
        "Python的**GIL**让多线程无法真正并行计算，但IO等待时会释放——所以线程对网络/文件类任务仍然提速显著。",
        "手写Thread原始API容易失控（线程数、结果收集、异常处理都是坑）；**ThreadPoolExecutor**把这一切打包成一行。",
    ],
    "core": [
        ("线程与进程", [
            "- 线程共享内存、轻量、切换快；进程隔离、重量、切换慢。",
            "- **GIL（全局解释器锁）**：同一时刻只有一个线程执行Python字节码→CPU计算多线程几乎不加速。",
            "- 结论：**IO密集用线程，CPU密集用多进程**。",
        ]),
        ("ThreadPoolExecutor", [
            "- executor.map(fn, items)：按输入顺序返回结果。",
            "- executor.submit(...) + as_completed(...)：按**完成顺序**取结果，谁先完先用谁。",
            "- with语句退出时自动等待全部任务结束并回收。",
        ]),
    ],
    "diagrams": [
        ("image", lambda: dg.flow_diagram(
            "线程池调度示意（4个任务, 2个工人）",
            ["提交任务 i=0..3", "工人1拿任务0，工人2拿任务1", "任务1先完成 → as_completed先返回1",
             "工人1拿任务2，工人2拿任务3", "全部完成, with退出自动join"], "day04_threadpool.png"),
         "map保序 vs as_completed按完成序"),
    ],
    "code": [
        ("线程池并发映射", (
            "from concurrent.futures import ThreadPoolExecutor\n"
            "\n"
            "def concurrent_map(func, items):\n"
            "    with ThreadPoolExecutor(max_workers=8) as pool:\n"
            "        return list(pool.map(func, items))  # 保输入顺序\n"
            "\n"
            "urls = ['a.png', 'b.png', 'c.png', 'd.png']\n"
            "results = concurrent_map(download, urls)   # 并行下载\n"),
         ["max_workers是同时干活的线程数上限，不是任务数。",
          "pool.map返回值顺序与items一致——想按完成序要用as_completed。",
          "with结束后所有线程已被回收，不会泄漏。"]),
    ],
    "practice": [
        "- **爬虫/下载/批量调用API**：线程池的标准战场。",
        "- **控制并发上限**：max_workers别写1000——对方服务器会封你。",
        "- **线程安全**：共享变量+=1在并发下有竞态；要么用锁，要么让每个任务只写自己的结果。",
        "- CPU密集（图像处理、矩阵运算）请换ProcessPoolExecutor——这正是Day15之前先记住的原则。",
    ],
    "mistakes": [
        {"q": "用4个线程跑矩阵乘法，比单线程还慢", "reason": "GIL下CPU计算无法并行，还多了切换开销", "fix": "CPU密集改用ProcessPoolExecutor或向量化(numpy/torch)"},
        {"q": "结果顺序和提交顺序对不上", "reason": "用了submit+as_completed却按提交序组装", "fix": "需要保序用map；需要先完先用才用as_completed"},
        {"q": "线程池忘了shutdown，进程卡住不退", "reason": "非daemon线程阻塞退出", "fix": "总是用with自动回收"},
    ],
    "summary": {
        "learned": ["线程与顺序执行的差异", "GIL与IO/CPU密集的分类", "map与as_completed的顺序语义"],
        "must": ["手写concurrent_map", "解释为什么多线程提速不了纯计算"],
    },
    "task_link": "对应 tasks/day04.json：run_in_threads/concurrent_map。挑战项make_process（多进程）为Day11-15的device与并行训练意识埋伏笔。",
},
# ------------------------------------------------------------------ Day05
{
    "day": 5,
    "title": "HTTP客户端与异常包装",
    "goal": "学完今天，你能够封装一个带URL拼接的API客户端，并把你调的第三方异常统一包装成自己的业务异常——这是调用一切在线服务的起点。",
    "why": [
        "天气预报、翻译、大模型……今天**几乎一切能力都以HTTP API形式提供**；会调API是AI工程师的基本功。",
        "requests抛出的异常五花八门（连接失败/超时/解码错误）；上层业务代码若逐一对付它们，就会满屏try/except。**包装成自己的APIError**，上层只处理一种异常。",
        "超时不设置，程序可能永远卡住；这就是为什么工程调用必须显式timeout。",
    ],
    "core": [
        ("URL与query参数", [
            "- URL构成：协议://主机/路径?参数；参数是键值对，如 ?city=beijing&day=3。",
            "- 用库函数拼参数而不是手拼字符串——空格/中文会自动编码。",
        ]),
        ("requests与异常", [
            "- GET取数据、POST带JSON提交；r.status_code判结果。",
            "- **RequestException是所有请求类异常的基类**——捕获它兜底。",
        ]),
        ("异常包装", [
            "- 自定义 APIError(Exception)；在客户端内部 try...except requests.RequestException → raise APIError(信息) from e。",
            "- 业务层只需 catch APIError，还能在包装时附上url等上下文。",
        ]),
    ],
    "diagrams": [
        ("image", lambda: dg.flow_diagram(
            "一次API调用的完整链路",
            ["业务代码调用 client.get('/weather')", "拼完整URL(含query)", "requests发起请求",
             "网络失败? → raise APIError(带上下文)", "成功 → 解析并返回数据"], "day05_apiflow.png"),
         "异常在客户端内部被统一翻译"),
    ],
    "code": [
        ("最小API客户端", (
            "import requests\n"
            "\n"
            "class APIError(Exception):\n"
            "    \"\"\"业务层唯一需要关心的异常\"\"\"\n"
            "\n"
            "class APIClient:\n"
            "    def __init__(self, base_url, timeout=5):\n"
            "        self.base_url = base_url.rstrip('/')\n"
            "        self.timeout = timeout\n"
            "\n"
            "    def get(self, path, params=None):\n"
            "        try:\n"
            "            r = requests.get(self.base_url + path,\n"
            "                             params=params, timeout=self.timeout)\n"
            "            r.raise_for_status()          # 4xx/5xx也当异常\n"
            "            return r.json()\n"
            "        except requests.RequestException as e:\n"
            "            raise APIError(f'{path} 请求失败: {e}') from e\n"),
         ["timeout写在构造参数里：工程调用永远要有超时。",
          "raise_for_status()让HTTP错误码也走异常通道，统一处理。",
          "from e保留原始异常链，traceback里能看到根因。"]),
    ],
    "practice": [
        "- **所有第三方SDK都这样包一层**：换供应商只改内部实现。",
        "- 包装异常时带上**上下文**（url/参数），排障效率翻倍。",
        "- 复杂项目在客户端层统一做**重试**（限流时的指数退避）——对应本日可选挑战。",
    ],
    "mistakes": [
        {"q": "except Exception 一网打尽却不处理", "reason": "吞掉异常=故障静默", "fix": "只捕获RequestException并转成APIError，别的异常让它爆"},
        {"q": "手拼URL参数，中文/空格请求出错", "reason": "没做URL编码", "fix": "用params=参数交给requests编码"},
        {"q": "没设timeout，某天程序卡死", "reason": "网络请求默认可能无限等待", "fix": "显式timeout，必要时配合重试"},
    ],
    "summary": {
        "learned": ["URL/query结构", "requests的GET/POST", "异常包装模式"],
        "must": ["写出带APIError的APIClient", "解释为什么timeout必须设置"],
    },
    "task_link": "对应 tasks/day05.json：build_url/APIClient/APIError。重试机制只放挑战项——先学会“正确地失败”，Day31会教“优雅地重试”。",
},
# ------------------------------------------------------------------ Day06
{
    "day": 6,
    "title": "Pandas数据清洗与NumPy数值处理",
    "goal": "学完今天，你能够把一份带缺失、带重复、量纲混乱的表格数据清洗成可训练的样子，并掌握min-max归一化。",
    "why": [
        "**Garbage In, Garbage Out**：喂给模型的数据有缺失值、重复行、量纲差一万倍，再好的模型也学不出东西。",
        "业界统计：真实项目里**80%的时间在数据处理**，只有20%在建模。这80%里Pandas是主力。",
        "归一化是大多数模型的共同前提——特征范围[0,100000]和[0,1]并存时，梯度下降会变成跳悬崖。",
    ],
    "core": [
        ("DataFrame与Series", [
            "- DataFrame=一张带列名的表；Series=其中一列。",
            "- 常用：df.head()、df.shape、df[col] 取值。",
        ]),
        ("清洗三连", [
            "- **dropna()** 删除含缺失值的行（模型不会补数，先删）。",
            "- **drop_duplicates()** 删除完全重复的行（重复数据会让模型“背书”）。",
            "- 排序无关紧要，先洗后看。",
        ]),
        ("NumPy数值辅助", [
            "- ndarray是数值计算底座：支持向量化，比Python循环快几十倍。",
            "- 本日用它做统计：min/max/mean——归一化的原料。",
        ]),
        ("min-max归一化", [
            "- 公式 (x - min) / (max - min)，把一列压到[0,1]。",
            "- **常数列陷阱**：max==min时分母为零——约定返回0.5或原样，不能除零崩掉。",
        ]),
    ],
    "diagrams": [
        ("image", lambda: dg.flow_diagram(
            "数据清洗流水线",
            ["读取原始DataFrame", "dropna 去掉缺失行", "drop_duplicates 去重复",
             "min-max归一化到[0,1]", "清洗率统计 → 交给模型"], "day06_cleaning.png"),
         "先洗再训，一步都不能跳"),
    ],
    "code": [
        ("清洗+归一化的最小实现", (
            "import pandas as pd\n"
            "\n"
            "def clean_dataframe(df):\n"
            "    df = df.dropna()              # 去缺失\n"
            "    df = df.drop_duplicates()    # 去重复\n"
            "    return df\n"
            "\n"
            "def minmax_normalize(df, column):\n"
            "    s = df[column]\n"
            "    lo, hi = s.min(), s.max()\n"
            "    if hi == lo:                 # 常数列防除零\n"
            "        return s * 0 + 0.5\n"
            "    return (s - lo) / (hi - lo)\n"),
         ["dropna/drop_duplicates返回新DataFrame，记得接住。",
          "常数列没有“尺度问题”，返回0.5是让管线不崩的约定。",
          "归一化后的列取值范围必在[0,1]——测试就验证这个。"]),
    ],
    "practice": [
        "- **先划分再清洗**：测试集不能用训练集的min/max去归一化（数据泄漏）。",
        "- 记录每次清洗删了多少行（清洗率），报告里讲得清。",
        "- 分类标签不归一化；数值特征才归一化。",
    ],
    "mistakes": [
        {"q": "用测试集的统计量归一化训练集", "reason": "数据泄漏：模型偷看了未来", "fix": "统计量只用训练集算，保存下来再套用到测试集"},
        {"q": "常数列归一化直接除零NaN蔓延", "reason": "没考虑max==min", "fix": "先判相等再归一化"},
        {"q": "df.dropna()后没赋值，原df没变", "reason": "Pandas默认返回副本", "fix": "df = df.dropna() 或传inplace参数(不推荐)"},
    ],
    "summary": {
        "learned": ["DataFrame/Series基本操作", "dropna/drop_duplicates", "min-max归一化与常数列处理"],
        "must": ["手写clean_dataframe", "说出归一化为什么是模型前提"],
    },
    "task_link": "对应 tasks/day06.json：clean_dataframe/minmax_normalize。本日的NumPy操作会在Day07向量化损失、Day11+的PyTorch里持续发光——数据手感是所有ML能力的底座。",
},
# ------------------------------------------------------------------ Day07
{
    "day": 7,
    "title": "线性回归与梯度下降",
    "goal": "学完今天，你能够手写线性回归的完整训练循环——损失函数、梯度计算、参数更新三件套，并真正理解“模型是怎么学会的”。",
    "why": [
        "**梯度下降是全部深度学习的引擎**：CNN、Transformer训练的本质都是今天这三步的加粗放大。",
        "只有亲手算过梯度、调过学习率，才会对“lr太大发散、太小爬不动”有直觉——这种直觉调参时千金难换。",
        "线性回归是最简单的可解释模型，也是很多业务（销量预测、定价）的基线方案。",
    ],
    "core": [
        ("模型与损失", [
            "- 模型：y_pred = w·x + b，w权重、b偏置。",
            "- **MSE损失** = mean((y_pred - y)²)，衡量“平均差多远”，越小越好。",
        ]),
        ("梯度与更新", [
            "- 梯度=损失对参数的**斜率**：dw = mean(2·(y_pred-y)·x)，db = mean(2·(y_pred-y))。",
            "- 更新规则：w -= lr·dw（沿负梯度方向挪一小步）。",
            "- **lr学习率**决定步长：太大越过谷底发散，太小几百年不收敛。",
        ]),
        ("训练循环", [
            "- 固定套路：算预测 → 算loss → 算梯度 → 更新参数 → 重复N次。",
            "- 收敛判据：loss不再明显下降，或预测误差进阈值。",
        ]),
    ],
    "diagrams": [
        ("image", lambda: dg.curve_diagram(
            "训练中Loss的典型走势（学习率合适）",
            list(range(8)), [4.5, 2.9, 1.8, 1.1, 0.7, 0.45, 0.3, 0.22], "day07_loss_curve.png"),
         "loss单调下降且越来越缓=在收敛"),
    ],
    "code": [
        ("最小训练循环（y = 2x + 1 的数据）", (
            "import numpy as np\n"
            "\n"
            "X = np.array([1., 2., 3., 4., 5.])\n"
            "y = np.array([3., 5., 7., 9., 11.])   # 真实规律 2x+1\n"
            "\n"
            "w, b, lr = 0.0, 0.0, 0.01\n"
            "for step in range(800):\n"
            "    y_pred = X * w + b                    # ① 前向\n"
            "    loss = ((y_pred - y) ** 2).mean()     # ② 算损失\n"
            "    dw = (2 * (y_pred - y) * X).mean()    # ③ 算梯度\n"
            "    db = (2 * (y_pred - y)).mean()\n"
            "    w -= lr * dw                          # ④ 更新\n"
            "    b -= lr * db\n"
            "print(f'w={w:.2f}, b={b:.2f}')            # → w=2.00, b=1.00\n"),
         ["X*w+b是向量化前向：一次算出全部预测，比for循环快且简洁。",
          "dw公式来自对loss求导（链式法则），今天先接受，Day09会用autograd自动算。",
          "800次迭代后w、b逼近真实值2和1——这就是“学会”。"]),
    ],
    "practice": [
        "- **lr调参顺序**：0.1→0.01→0.001各试一轮，看loss曲线选择。",
        "- 训练前**归一化输入**（Day06技能），否则不同尺度特征梯度差千倍。",
        "- 每100步打印一次loss，肉眼判断发散/收敛/爬不动。",
    ],
    "mistakes": [
        {"q": "lr=1.0，loss越训越大直到inf", "reason": "步长太大，跳过了谷底", "fix": "把lr降一个数量级重试"},
        {"q": "参数永远收敛不到真值附近", "reason": "迭代次数不够或lr太小", "fix": "增大迭代次数，观察loss是否还在下降"},
        {"q": "X是列表，X*w直接报错", "reason": "列表没有向量化运算", "fix": "统一用numpy数组参与计算"},
    ],
    "summary": {
        "learned": ["MSE损失", "dw/db梯度公式", "w -= lr·dw更新规则", "训练循环四步"],
        "must": ["手写线性回归训练循环", "解释lr过大过小的两种失败模式"],
    },
    "task_link": "对应 tasks/day07.json：mse_loss/LinearRegression(fit/predict)。任务给的90分钟里20分钟留给公式推导是刻意设计——推导一遍，后面39天都在吃今天的红利。",
},
# ------------------------------------------------------------------ Day08
{
    "day": 8,
    "title": "PyTorch Tensor入门",
    "goal": "学完今天，你能够创建、改形、统计、索引张量，并理解dtype/device/shape三要素——它们是所有PyTorch代码的“身份证”。",
    "why": [
        "**Tensor是PyTorch的一等公民**：模型参数、输入数据、梯度全是张量；不懂张量，后面每一天都是空中楼阁。",
        "张量=带GPU加速的numpy数组；同样的数值运算，搬上GPU能快两个数量级。",
        "90%的PyTorch报错最终都是**三要素问题**：shape对不上、dtype不匹配、device不一致。",
    ],
    "core": [
        ("三要素", [
            "- **shape**：各维长度，如(2,3)；改形用reshape，总元素数必须守恒。",
            "- **dtype**：数值类型；深度学习默认float32——很多模型权重就是这个精度。",
            "- **device**：cpu/cuda；张量与模型必须同设备才能一起算。",
        ]),
        ("创建与操作", [
            "- torch.tensor(data, dtype=...)、torch.zeros/randn。",
            "- 统计：t.mean()/t.std()；索引：t[0]、t[:, -1]。",
            "- 索引取出的是**视图还是副本**要留意（浅拷贝陷阱）。",
        ]),
    ],
    "diagrams": [
        ("ascii", (
            "t = torch.randn(2, 3)     ← shape(2,3), dtype=float32, device=cpu\n"
            "┌               ┐\n"
            "│ 0.3  -0.1  1.2 │   ← 第0行 (batch第0个样本)\n"
            "│ 0.8   0.0 -0.5 │   ← 第1行\n"
            "└               ┘\n"
            "t.reshape(3, 2) 合法(元素数都是6);  t.reshape(2, 4) 报错\n"),
         "张量三要素：shape/dtype/device"),
    ],
    "code": [
        ("张量最小操作集", (
            "import torch\n"
            "\n"
            "t = torch.tensor([[1, 2, 3], [4, 5, 6]],\n"
            "                 dtype=torch.float32)   # (2,3)\n"
            "print(t.shape, t.dtype, t.device)\n"
            "\n"
            "r = t.reshape(3, 2)      # 元素守恒, 合法\n"
            "m, s = t.mean(), t.std() # 统计\n"
            "last = t.flatten()[-1]   # 展平后取最后一个元素\n"),
         ["创建时显式dtype=torch.float32——默认int的tensor后面算均值会报类型错。",
          "reshape后与reshape前共享存储，改一个另一个也变（视图）。",
          "t.device在没装CUDA的机器上永远是cpu——先记住这个事实。"]),
    ],
    "practice": [
        "- **训练前统一三要素**：输入/标签/模型 weight 的dtype与device必须一致。",
        "- **打印诊断**：报shape错误时第一时间print(x.shape)。",
        "- 习惯用 float32 + cpu 起步，模型跑通再上GPU——顺序别反。",
    ],
    "mistakes": [
        {"q": "RuntimeError: expected scalar type Float but found Long", "reason": "dtype不一致(int64 vs float32)", "fix": "创建时或通过t.float()统一dtype"},
        {"q": "reshape报错元素数不匹配", "reason": "新shape乘积≠元素总数", "fix": "先print(t.shape)核对，再算目标shape"},
        {"q": "CPU张量与cuda张量相加减报错", "reason": "device不一致", "fix": "用.to(device)统一搬移（Day11详讲）"},
    ],
    "summary": {
        "learned": ["三要素shape/dtype/device", "reshape守恒", "mean/std统计", "索引与展平"],
        "must": ["创建并读出任意张量的三要素", "说出最常见的三种张量报错类型"],
    },
    "task_link": "对应 tasks/day08.json：create_tensor/reshape_tensor/tensor_stats/index_last。这是PyTorch第一课，任务刻意小——把三要素刻进肌肉记忆，Day09自动求导才有落脚点。",
},
# ------------------------------------------------------------------ Day09
{
    "day": 9,
    "title": "Autograd自动求导",
    "goal": "学完今天，你能够用requires_grad+backward自动算出任意可微函数的梯度，并理解梯度累积机制——从此告别手推梯度公式。",
    "why": [
        "Day07手推dw/db只对线性回归可行；面对千万参数的模型，**手算梯度在数学上就不现实**。",
        "Autograd在计算过程中悄悄构建**计算图**，backward时沿图反向传播——这就是深度学习框架存在的第一理由。",
        "理解梯度是“累积”而非“覆盖”，能避免训练中最隐蔽的一类bug。",
    ],
    "core": [
        ("开启求导", [
            "- 创建叶子张量时设 **requires_grad=True**。",
            "- 对最终输出（必须是**标量**）调用 backward()。",
            "- 梯度存放在 x.grad 里。",
        ]),
        ("计算图与链式法则", [
            "- 前向时每个运算被记录成节点：y = a·x²+b·x+c 就是一张小图。",
            "- backward按图反向走一遍链式法则，每个节点拿到自己的梯度。",
        ]),
        ("梯度累积", [
            "- 对同一个图连续两次backward，grad会**相加**而不是覆盖。",
            "- 训练循环里因此必须先 zero_grad()（Day12会正式用到）。",
        ]),
    ],
    "diagrams": [
        ("image", lambda: dg.computation_graph("autograd_graph.png"),
         "计算图：backward沿箭头反推梯度"),
    ],
    "code": [
        ("自动求二次函数在某点的梯度", (
            "import torch\n"
            "\n"
            "def grad_of_quadratic(a, b, c, x_value):\n"
            "    x = torch.tensor(x_value, requires_grad=True)\n"
            "    y = a * x ** 2 + b * x + c     # 前向: 边算边记录计算图\n"
            "    y.backward()                    # 反向: 自动算 dy/dx\n"
            "    return x.grad\n"
            "\n"
            "# f(x)=2x²+x 在 x=3 处梯度 = 2*2*3+1 = 13\n"
            "print(grad_of_quadratic(2.0, 1.0, 0.0, 3.0))   # tensor(13.)\n"),
         ["requires_grad=True把x标记为“我要对它求导”。",
          "y是标量才能直接backward；向量要先.sum()成标量。",
          "返回x.grad：梯度是张量，取出数值用.item()或float()。"]),
    ],
    "practice": [
        "- **推理阶段关掉求导**：torch.no_grad() 或 model.eval()，省内存还快。",
        "- **训练前zero_grad**：不清零就会把上一轮的梯度累加进来。",
        "- 需要梯度数值出图时用 .detach()，防止意外传播。",
    ],
    "mistakes": [
        {"q": "backward报错: grad can be implicitly created only for scalar outputs", "reason": "对向量直接backward", "fix": "先.sum()或.mean()成标量再backward"},
        {"q": "训练loss不收敛，梯度是预期值的两倍", "reason": "两次backward未清零，梯度累积", "fix": "每次更新前optimizer.zero_grad()"},
        {"q": "想打印梯度却把计算图带出了no_grad", "reason": "没理解grad会留在图上", "fix": "打印用x.grad.item()，保存用.detach()"},
    ],
    "summary": {
        "learned": ["requires_grad/backward/grad三连", "计算图概念", "梯度累积机制"],
        "must": ["算出二次函数任意点的梯度", "解释为什么训练要zero_grad"],
    },
    "task_link": "对应 tasks/day09.json：quadratic/gradient_at/nested_fn。任务的梯度累积验证（两次backward后grad翻倍）就是本日最容易错的知识点，务必亲手踩一次。",
},
# ------------------------------------------------------------------ Day10
{
    "day": 10,
    "title": "nn.Module与第一个神经网络",
    "goal": "学完今天，你能够继承nn.Module搭出多层感知机（MLP），计算模型参数量，并选择合适的激活函数——从公式时代进入网络时代。",
    "why": [
        "手写w、b到第10个参数就崩了；**nn.Module把参数、结构、前向打包成对象**，千层网络也只是几行声明。",
        "神经网络=线性层+激活的堆叠；没有激活函数，再深的网络也只是一个大线性变换。",
        "参数量=模型“脑容量”的度量，也是选模型/算显存的第一指标。",
    ],
    "core": [
        ("nn.Module", [
            "- 继承它，__init__里声明层，forward里定义数据流。",
            "- **Linear(in, out)**=全连接层，内部含weight与bias，是自动被登记的参数。",
            "- model.parameters() 遍历全部可训练参数。",
        ]),
        ("激活函数", [
            "- **ReLU**：负值归零，正值放行——当前默认选择。",
            "- Sigmoid：压到(0,1)，多用于输出概率；Tanh：(-1,1)。",
            "- 激活让网络能拟合非线性——没有它只能画直线。",
        ]),
        ("参数量", [
            "- Linear(in,out)：weight in×out + bias out 个。",
            "- 逐层相加即可，含bias。",
        ]),
    ],
    "diagrams": [
        ("image", lambda: dg.mlp_diagram("mlp.png"),
         "MLP：输入→隐层(ReLU)→输出"),
    ],
    "code": [
        ("三层的MLP", (
            "import torch.nn as nn\n"
            "\n"
            "class MLP(nn.Module):\n"
            "    def __init__(self, in_features, hidden, out_features):\n"
            "        super().__init__()\n"
            "        self.fc1 = nn.Linear(in_features, hidden)\n"
            "        self.relu = nn.ReLU()\n"
            "        self.fc2 = nn.Linear(hidden, out_features)\n"
            "\n"
            "    def forward(self, x):\n"
            "        x = self.relu(self.fc1(x))   # 线性→激活\n"
            "        x = self.fc2(x)              # 输出层(默认不激活)\n"
            "        return x\n"
            "\n"
            "model = MLP(4, 8, 2)\n"
            "print(sum(p.numel() for p in model.parameters()))\n"),
         ["super().__init__()必须第一行——Module注册机制依赖它。",
          "层定义在__init__，前向流程写forward——参数与逻辑分离。",
          "输出层一般不加激活，配合交叉熵损失用logits（Day12会讲）。"]),
    ],
    "practice": [
        "- **参数量先行**：搭完先print参数量，判断模型规模是否合理。",
        "- **模块可嵌套**：MLP可以再装进更大的网络当组件。",
        "- 输入batch的shape约定 (B, features)：第0维永远是批大小。",
    ],
    "mistakes": [
        {"q": "忘了super().__init__()，参数注册混乱", "reason": "Module的初始化机制没执行", "fix": "__init__第一行写super().__init__()"},
        {"q": "forward里用 nn.ReLU(x) 逐次新建", "reason": "把激活当函数用了", "fix": "激活在__init__声明为self.relu，forward复用"},
        {"q": "参数量对不上预期", "reason": "漏算了bias", "fix": "Linear参数=in*out(weight)+out(bias)"},
    ],
    "summary": {
        "learned": ["nn.Module结构", "Linear与ReLU", "参数量计算", "激活函数选择"],
        "must": ["搭出MLP并算对参数量", "解释没有激活函数会发生什么"],
    },
    "task_link": "对应 tasks/day10.json：MLP/count_parameters/build_activation。任务里的forward形状断言(B,out_features)是后续所有网络测试的模板——今天把它养成习惯，Day13的CNN只是换层不换思路。",
},
    ],
}
