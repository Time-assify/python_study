"""AI Engineer Training Platform - 完整学习系统"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.task_manager import TaskManager
from src.evaluator import CodeExecutor, TestEngine
from src.agents import DeepSeekAgent, LearningAgent
from src.database import Database
from src.llm import LLMClient
from src.rag import KnowledgeBase
from src.submission_manager import SubmissionManager
from src.utils.helpers import Helpers


class LearningSystem:
    """AI学习系统
    
    提供完整的学习流程：
    1. 查看每日任务
    2. 学习理论知识
    3. 编写代码
    4. 提交评测
    5. 获取AI反馈
    6. 查看学习进度
    """
    
    def __init__(self):
        """初始化学习系统"""
        self.task_manager = TaskManager()
        self.code_executor = CodeExecutor()
        self.test_engine = TestEngine()
        self.llm_client = LLMClient()
        self.deepseek_agent = DeepSeekAgent(self.llm_client)
        self.learning_agent = LearningAgent(self.llm_client)
        self.database = Database()
        self.submission_manager = SubmissionManager()
        self.knowledge_base = KnowledgeBase()
        
        self.current_day = 1
        self.user_name = "学员"
    
    def start(self):
        """启动学习系统"""
        self._clear_screen()
        self._show_welcome()
        
        while True:
            self._show_main_menu()
            choice = input("\n请选择操作 (0-8): ").strip()
            
            if choice == "0":
                self._show_goodbye()
                break
            elif choice == "1":
                self._view_today_task()
            elif choice == "2":
                self._submit_code()
            elif choice == "3":
                self._view_progress()
            elif choice == "4":
                self._view_learning_history()
            elif choice == "5":
                self._generate_report()
            elif choice == "6":
                self._view_statistics()
            elif choice == "7":
                self._set_current_day()
            elif choice == "8":
                self._search_knowledge()
            else:
                Helpers.print_error("无效的选择，请重新输入")
    
    def _clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _show_welcome(self):
        """显示欢迎信息"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           🎓 AI Engineer Training Platform v2.0              ║
║                                                              ║
║              40天AI工程师训练系统                             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        # 加载用户进度
        self._load_progress()
        
        print(f"欢迎回来，{self.user_name}！")
        print(f"当前进度：Day {self.current_day}/40")
        
        phase_info = Helpers.get_phase_info(self.current_day)
        print(f"当前阶段：{phase_info['name']}")
        
        input("\n按Enter键继续...")
    
    def _show_main_menu(self):
        """显示主菜单"""
        self._clear_screen()
        
        phase_info = Helpers.get_phase_info(self.current_day)
        progress = self.database.get_progress(self.current_day)
        score = progress.score if progress else 0
        
        print("=" * 60)
        print(f"📚 Day {self.current_day}: {phase_info['name']}阶段 | 当前分数: {score:.1f}")
        print("=" * 60)
        print()
        print("1. 📋 查看今日任务")
        print("2. 💻 提交代码评测")
        print("3. 📈 查看学习进度")
        print("4. 📜 查看学习历史")
        print("5. 📊 生成学习报告")
        print("6. 📉 查看详细统计")
        print("7. ⚙️  设置当前天数")
        print("8. 🔍 搜索知识库")
        print("0. 🚪 退出系统")
        print()
        print("=" * 60)
    
    def _view_today_task(self):
        """查看今日任务"""
        self._clear_screen()
        
        task = self.task_manager.get_task(self.current_day)
        if not task:
            Helpers.print_error(f"Day {self.current_day} 的任务不存在")
            input("按Enter键返回...")
            return
        
        phase_info = Helpers.get_phase_info(self.current_day)
        
        print("=" * 60)
        print(f"📋 Day {self.current_day}: {task.title}")
        print("=" * 60)
        print()
        print(f"🎯 学习目标: {task.goal}")
        print(f"📝 任务: {task.task}")
        print()
        print("📖 任务描述:")
        print("-" * 40)
        print(task.description)
        print("-" * 40)
        print()
        
        if task.tests:
            print("🧪 测试要求:")
            for test in task.tests:
                print(f"   ✓ {test}")
            print()
        
        if task.hints:
            print("💡 提示:")
            for hint in task.hints:
                print(f"   • {hint}")
            print()
        
        if task.resources:
            print("📚 学习资源:")
            for resource in task.resources:
                print(f"   🔗 {resource}")
            print()
        
        # 显示提交目录
        submit_dir = Path("submissions") / f"day{self.current_day:02d}"
        print(f"📁 代码提交目录: {submit_dir}")
        print(f"📄 提交文件: {submit_dir}/answer.py")
        print()
        
        input("按Enter键返回...")
    
    def _submit_code(self):
        """提交代码"""
        self._clear_screen()
        
        print("=" * 60)
        print("💻 提交代码评测")
        print("=" * 60)
        print()
        
        # 获取代码文件路径
        submit_dir = Path("submissions") / f"day{self.current_day:02d}"
        default_file = submit_dir / "answer.py"
        
        file_path = input(f"代码文件路径 (默认: {default_file}): ").strip()
        if not file_path:
            file_path = str(default_file)
        
        if not Path(file_path).exists():
            Helpers.print_error(f"文件不存在: {file_path}")
            input("按Enter键返回...")
            return
        
        # 读取代码
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            Helpers.print_error(f"读取文件失败: {e}")
            input("按Enter键返回...")
            return
        
        print("\n🔍 正在验证代码语法...")
        validation = self.code_executor.validate_code(code)
        if not validation["valid"]:
            Helpers.print_error(f"语法错误: {validation['message']}")
            input("按Enter键返回...")
            return
        
        Helpers.print_success("语法验证通过")
        
        print("\n⚙️ 正在执行代码...")
        result = self.code_executor.execute_code(code)
        
        if result.status == "success":
            Helpers.print_success(f"代码执行成功 (耗时: {result.time:.2f}秒)")
            if result.stdout:
                print(f"\n输出:\n{result.stdout[:500]}")
        else:
            Helpers.print_error(f"代码执行失败:")
            print(result.stderr[:500])
            input("\n按Enter键返回...")
            return
        
        # 保存提交
        self.submission_manager.submit_code(
            day=self.current_day,
            code=code,
            score=0
        )
        
        # 运行测试
        print("\n🧪 正在运行测试...")
        
        # 检查是否有对应的测试文件
        test_file = Path("tests") / f"day{self.current_day:02d}_test.py"
        if test_file.exists():
            test_result = self.test_engine.run_tests(str(test_file))
        else:
            test_result = self.test_engine.run_tests()
        
        print(f"测试结果: {test_result.passed}/{test_result.total_tests} 通过")
        print(f"测试分数: {test_result.score:.1f}")
        
        # AI审查
        print("\n🤖 正在进行AI代码审查...")
        task = self.task_manager.get_task(self.current_day)
        
        review_result = self.deepseek_agent.review_code(
            code,
            task.description if task else "",
            str(test_result.to_dict()),
            test_result.score
        )
        
        # 计算综合分数
        final_score = test_result.score * 0.5 + review_result.score * 0.5
        
        # 保存到数据库
        from src.database.db import ProgressRecord, SubmissionRecord
        
        progress = ProgressRecord(
            day=self.current_day,
            score=final_score,
            test_result=test_result.to_dict(),
            ai_review=review_result.to_dict()
        )
        self.database.save_progress(progress)
        
        # 显示结果
        print("\n" + "=" * 60)
        print("📊 评测结果")
        print("=" * 60)
        print(f"测试分数: {test_result.score:.1f}")
        print(f"AI评分: {review_result.score:.1f}")
        print(f"综合分数: {Helpers.format_score(final_score)}")
        print()
        
        if review_result.bugs:
            print("🐛 发现的问题:")
            for bug in review_result.bugs:
                print(f"   • {bug}")
            print()
        
        if review_result.suggestions:
            print("💡 改进建议:")
            for suggestion in review_result.suggestions:
                print(f"   • {suggestion}")
            print()
        
        if review_result.next_learning:
            print(f"📚 下一步学习建议: {review_result.next_learning}")
        
        # 更新分数
        self.submission_manager.submit_code(
            day=self.current_day,
            code=code,
            score=final_score
        )
        
        input("\n按Enter键返回...")
    
    def _view_progress(self):
        """查看学习进度"""
        self._clear_screen()
        
        print("=" * 60)
        print("📈 学习进度")
        print("=" * 60)
        print()
        
        # 获取统计数据
        stats = self.database.get_learning_statistics()
        
        print(f"📊 总体统计:")
        print(f"   已完成天数: {stats.get('completed_days', 0)}/40")
        print(f"   完成率: {stats.get('completion_rate', 0):.1f}%")
        print(f"   平均分: {stats.get('average_score', 0):.1f}")
        print(f"   最高分: {stats.get('max_score', 0):.1f}")
        print(f"   总提交次数: {stats.get('total_submissions', 0)}")
        print()
        
        # 显示进度条
        progress = stats.get('completed_days', 0) / 40
        bar_length = 40
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"学习进度: [{bar}] {progress*100:.1f}%")
        print()
        
        # 显示各阶段完成情况
        print("📚 各阶段完成情况:")
        for phase in range(1, 5):
            phase_info = Helpers.get_phase_info(1)
            phase_tasks = self.task_manager.get_phase_tasks(phase)
            completed = sum(1 for t in phase_tasks 
                          if self.database.get_progress(t.day) is not None)
            total = len(phase_tasks)
            
            phase_names = {1: "Python工程", 2: "PyTorch", 3: "深度学习", 4: "AI Agent"}
            print(f"   {phase_names[phase]}: {completed}/{total}")
        
        print()
        input("按Enter键返回...")
    
    def _view_learning_history(self):
        """查看学习历史"""
        self._clear_screen()
        
        print("=" * 60)
        print("📜 学习历史")
        print("=" * 60)
        print()
        
        progress_list = self.database.get_all_progress()
        
        if not progress_list:
            print("暂无学习记录")
            input("\n按Enter键返回...")
            return
        
        print(f"{'Day':<6} {'分数':<10} {'状态':<10} {'时间'}")
        print("-" * 60)
        
        for progress in progress_list[-20:]:  # 显示最近20条
            status = "✓ 通过" if progress.score >= 60 else "✗ 未通过"
            time_str = progress.timestamp[:10] if progress.timestamp else "N/A"
            print(f"{progress.day:<6} {progress.score:<10.1f} {status:<10} {time_str}")
        
        print()
        input("按Enter键返回...")
    
    def _generate_report(self):
        """生成学习报告"""
        self._clear_screen()
        
        print("=" * 60)
        print("📊 生成学习报告")
        print("=" * 60)
        print()
        
        progress_list = self.database.get_all_progress()
        stats = self.database.get_learning_statistics()
        
        if not progress_list:
            print("暂无学习记录，无法生成报告")
            input("\n按Enter键返回...")
            return
        
        # 使用AI生成报告
        if self.llm_client.is_available():
            print("🤖 正在使用AI生成详细报告...")
            response = self.llm_client.generate_report(
                {"progress": [p.to_dict() for p in progress_list]},
                stats
            )
            
            if response:
                print(response.content)
            else:
                self._print_simple_report(progress_list, stats)
        else:
            self._print_simple_report(progress_list, stats)
        
        # 保存报告到文件
        report_dir = Path("reports")
        report_dir.mkdir(exist_ok=True)
        
        report_file = report_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        report_content = f"""# AI工程师训练报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 总体统计

- 已完成天数: {stats.get('completed_days', 0)}/40
- 完成率: {stats.get('completion_rate', 0):.1f}%
- 平均分: {stats.get('average_score', 0):.1f}
- 最高分: {stats.get('max_score', 0):.1f}
- 总提交次数: {stats.get('total_submissions', 0)}

## 学习记录

| Day | 分数 | 状态 |
|-----|------|------|
"""
        
        for progress in progress_list:
            status = "通过" if progress.score >= 60 else "未通过"
            report_content += f"| {progress.day} | {progress.score:.1f} | {status} |\n"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\n📄 报告已保存到: {report_file}")
        input("\n按Enter键返回...")
    
    def _print_simple_report(self, progress_list, stats):
        """打印简单报告"""
        print("📊 学习报告")
        print("-" * 40)
        print(f"学习进度: {stats.get('completed_days', 0)}/40天")
        print(f"平均分: {stats.get('average_score', 0):.1f}")
        print(f"最高分: {stats.get('max_score', 0):.1f}")
        
        # 分析趋势
        scores = [p.score for p in progress_list]
        if len(scores) >= 2:
            trend = self.learning_agent._analyze_trend(scores)
            if trend == "improving":
                print("学习趋势: 📈 进步中")
            elif trend == "declining":
                print("学习趋势: 📉 需要加强")
            else:
                print("学习趋势: ➡️ 稳定")
    
    def _view_statistics(self):
        """查看详细统计"""
        self._clear_screen()
        
        print("=" * 60)
        print("📉 详细统计")
        print("=" * 60)
        print()
        
        # 获取学习推荐
        progress_list = self.database.get_all_progress()
        recommendation = self.learning_agent.get_learning_recommendation(
            self.current_day,
            [p.to_dict() for p in progress_list]
        )
        
        print("🎯 学习分析:")
        print(f"   难度调整: {recommendation.difficulty_adjustment}")
        print()
        
        if recommendation.weak_points:
            print("⚠️ 薄弱环节:")
            for point in recommendation.weak_points:
                print(f"   • {point}")
            print()
        
        if recommendation.recommended_review:
            print("📚 推荐复习:")
            for review in recommendation.recommended_review:
                print(f"   • {review}")
            print()
        
        if recommendation.next_tasks:
            print("🎯 下一步建议:")
            for task in recommendation.next_tasks:
                print(f"   • {task}")
        
        print()
        input("按Enter键返回...")
    
    def _set_current_day(self):
        """设置当前天数"""
        self._clear_screen()
        
        print("=" * 60)
        print("⚙️ 设置当前天数")
        print("=" * 60)
        print()
        
        day_input = input(f"请输入当前天数 (1-40, 当前: {self.current_day}): ").strip()
        
        try:
            day = int(day_input)
            if 1 <= day <= 40:
                self.current_day = day
                self._save_progress()
                Helpers.print_success(f"已设置为 Day {day}")
            else:
                Helpers.print_error("天数必须在1-40之间")
        except ValueError:
            Helpers.print_error("请输入有效的数字")
        
        input("\n按Enter键返回...")
    
    def _search_knowledge(self):
        """搜索知识库"""
        self._clear_screen()
        
        print("=" * 60)
        print("🔍 搜索知识库")
        print("=" * 60)
        print()
        
        query = input("请输入搜索关键词: ").strip()
        
        if not query:
            Helpers.print_error("搜索关键词不能为空")
            input("\n按Enter键返回...")
            return
        
        results = self.knowledge_base.search(query, top_k=5)
        
        if results:
            print(f"\n找到 {len(results)} 条相关结果:")
            print("-" * 40)
            
            for i, result in enumerate(results, 1):
                print(f"\n{i}. [相似度: {result['score']:.2f}]")
                print(f"   {result['content'][:200]}...")
        else:
            print("未找到相关结果")
        
        print()
        input("按Enter键返回...")
    
    def _load_progress(self):
        """加载进度"""
        progress_file = Path("data") / "user_progress.json"
        
        if progress_file.exists():
            with open(progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.current_day = data.get("current_day", 1)
                self.user_name = data.get("user_name", "学员")
    
    def _save_progress(self):
        """保存进度"""
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        progress_file = data_dir / "user_progress.json"
        
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump({
                "current_day": self.current_day,
                "user_name": self.user_name,
                "last_update": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    
    def _show_goodbye(self):
        """显示 goodbye 信息"""
        self._save_progress()
        
        self._clear_screen()
        print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║                    👋 感谢使用AI学习系统                     ║
║                                                              ║
║               继续加油，成为AI工程师！                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)


def main():
    """主函数"""
    # 设置UTF-8编码（仅在直接运行时）
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    system = LearningSystem()
    system.start()


if __name__ == "__main__":
    main()