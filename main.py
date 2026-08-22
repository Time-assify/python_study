"""AI Engineer Training Platform - 主入口"""
import sys
import argparse
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.task_manager import TaskManager
from src.evaluator import CodeExecutor, TestEngine
from src.agents import DeepSeekAgent, LearningAgent
from src.database import Database
from src.llm import LLMClient
from src.utils.helpers import Helpers


class TrainingPlatform:
    """训练平台主类"""
    
    def __init__(self):
        """初始化平台"""
        self.task_manager = TaskManager()
        self.code_executor = CodeExecutor()
        self.test_engine = TestEngine()
        self.llm_client = LLMClient()
        self.deepseek_agent = DeepSeekAgent(self.llm_client)
        self.learning_agent = LearningAgent(self.llm_client)
        self.database = Database()
        
    def show_menu(self):
        """显示主菜单"""
        Helpers.print_header("AI Engineer Training Platform v2.0")
        print("1. 查看今日任务")
        print("2. 提交代码")
        print("3. 运行测试")
        print("4. 查看学习进度")
        print("5. 查看学习报告")
        print("6. 设置")
        print("0. 退出")
        Helpers.print_separator()
        
    def show_task(self, day: int):
        """显示任务详情"""
        task = self.task_manager.get_task(day)
        if not task:
            Helpers.print_error(f"Day {day} 的任务不存在")
            return
        
        phase_info = Helpers.get_phase_info(day)
        
        Helpers.print_header(f"Day {day}: {task.title}")
        print(f"阶段: {phase_info['name']}")
        print(f"目标: {task.goal}")
        print(f"\n任务描述:")
        print(task.description)
        print(f"\n测试要求:")
        for test in task.tests:
            print(f"  - {test}")
        
        if task.hints:
            print(f"\n提示:")
            for hint in task.hints:
                print(f"  - {hint}")
        
        if task.resources:
            print(f"\n资源:")
            for resource in task.resources:
                print(f"  - {resource}")
    
    def submit_code(self, day: int, file_path: str):
        """提交代码"""
        # 检查文件是否存在
        if not Path(file_path).exists():
            Helpers.print_error(f"文件不存在: {file_path}")
            return
        
        # 读取代码
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 验证代码语法
        validation = self.code_executor.validate_code(code)
        if not validation["valid"]:
            Helpers.print_error(f"代码语法错误: {validation['message']}")
            return
        
        # 执行代码
        Helpers.print_info("正在执行代码...")
        result = self.code_executor.execute_code(code)
        
        if result.status == "success":
            Helpers.print_success(f"代码执行成功 (耗时: {result.time:.2f}秒)")
        else:
            Helpers.print_error(f"代码执行失败: {result.stderr}")
            return
        
        # 运行测试
        Helpers.print_info("正在运行测试...")
        test_result = self.test_engine.run_tests()
        
        # AI审查
        Helpers.print_info("正在进行AI审查...")
        task = self.task_manager.get_task(day)
        review_result = self.deepseek_agent.review_code(
            code, 
            task.description if task else "",
            str(test_result.to_dict()),
            test_result.score
        )
        
        # 保存到数据库
        from src.database.db import ProgressRecord, SubmissionRecord
        
        # 保存提交记录
        submission = SubmissionRecord(
            day=day,
            file_path=file_path,
            score=review_result.score
        )
        self.database.save_submission(submission)
        
        # 保存进度记录
        progress = ProgressRecord(
            day=day,
            score=review_result.score,
            test_result=test_result.to_dict(),
            ai_review=review_result.to_dict()
        )
        self.database.save_progress(progress)
        
        # 显示结果
        Helpers.print_separator()
        print(f"测试结果: {test_result.passed}/{test_result.total_tests} 通过")
        print(f"测试分数: {test_result.score:.1f}")
        print(f"AI评分: {review_result.score:.1f}")
        print(f"综合分数: {review_result.score:.1f}")
        
        if review_result.bugs:
            print(f"\n发现的问题:")
            for bug in review_result.bugs:
                print(f"  - {bug}")
        
        if review_result.suggestions:
            print(f"\n改进建议:")
            for suggestion in review_result.suggestions:
                print(f"  - {suggestion}")
        
        if review_result.next_learning:
            print(f"\n下一步学习建议: {review_result.next_learning}")
    
    def show_progress(self):
        """显示学习进度"""
        progress_list = self.database.get_all_progress()
        stats = self.database.get_learning_statistics()
        
        Helpers.print_header("学习进度统计")
        print(f"已完成天数: {stats.get('completed_days', 0)}/40")
        print(f"完成率: {stats.get('completion_rate', 0):.1f}%")
        print(f"平均分: {stats.get('average_score', 0):.1f}")
        print(f"最高分: {stats.get('max_score', 0):.1f}")
        print(f"总提交次数: {stats.get('total_submissions', 0)}")
        
        if progress_list:
            print(f"\n最近学习记录:")
            for progress in progress_list[-5:]:  # 显示最近5条
                print(f"  Day {progress.day}: {progress.score:.1f}分")
    
    def show_report(self):
        """显示学习报告"""
        progress_list = self.database.get_all_progress()
        stats = self.database.get_learning_statistics()
        
        if not progress_list:
            Helpers.print_warning("暂无学习记录")
            return
        
        Helpers.print_header("学习报告")
        
        # 使用AI生成报告
        if self.llm_client.is_available():
            Helpers.print_info("正在生成AI报告...")
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
    
    def _print_simple_report(self, progress_list, stats):
        """打印简单报告"""
        print(f"学习进度: {stats.get('completed_days', 0)}/40天")
        print(f"平均分: {stats.get('average_score', 0):.1f}")
        
        # 分析趋势
        scores = [p.score for p in progress_list]
        if len(scores) >= 2:
            trend = self.learning_agent._analyze_trend(scores)
            if trend == "improving":
                print("学习趋势: 进步中")
            elif trend == "declining":
                print("学习趋势: 需要加强")
            else:
                print("学习趋势: 稳定")
    
    def run(self):
        """运行平台"""
        while True:
            self.show_menu()
            choice = input("请选择操作 (0-6): ").strip()
            
            if choice == "0":
                Helpers.print_info("感谢使用，再见！")
                break
            elif choice == "1":
                day = int(input("请输入天数 (1-40): ").strip())
                if Helpers.validate_day(day):
                    self.show_task(day)
                else:
                    Helpers.print_error("无效的天数")
            elif choice == "2":
                day = int(input("请输入天数 (1-40): ").strip())
                file_path = input("请输入代码文件路径: ").strip()
                if Helpers.validate_day(day):
                    self.submit_code(day, file_path)
                else:
                    Helpers.print_error("无效的天数")
            elif choice == "3":
                Helpers.print_info("正在运行所有测试...")
                result = self.test_engine.run_tests()
                print(f"测试完成: {result.passed}/{result.total_tests} 通过")
                print(f"分数: {result.score:.1f}")
            elif choice == "4":
                self.show_progress()
            elif choice == "5":
                self.show_report()
            elif choice == "6":
                Helpers.print_info("设置功能开发中...")
            else:
                Helpers.print_error("无效的选择")
            
            input("\n按Enter键继续...")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AI Engineer Training Platform")
    parser.add_argument("--task", type=int, help="查看指定天的任务")
    parser.add_argument("--submit", nargs=2, metavar=("DAY", "FILE"), help="提交代码")
    parser.add_argument("--test", action="store_true", help="运行测试")
    parser.add_argument("--progress", action="store_true", help="查看学习进度")
    parser.add_argument("--report", action="store_true", help="查看学习报告")
    
    args = parser.parse_args()
    
    platform = TrainingPlatform()
    
    if args.task:
        platform.show_task(args.task)
    elif args.submit:
        day, file_path = args.submit
        platform.submit_code(int(day), file_path)
    elif args.test:
        result = platform.test_engine.run_tests()
        print(f"测试完成: {result.passed}/{result.total_tests} 通过")
        print(f"分数: {result.score:.1f}")
    elif args.progress:
        platform.show_progress()
    elif args.report:
        platform.show_report()
    else:
        platform.run()


if __name__ == "__main__":
    main()