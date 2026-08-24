"""AI Engineer Training Platform - CLI Entry"""
import os
import sys
import argparse
import io
from pathlib import Path

# Set UTF-8 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.platform import TrainingPlatform
from src.evaluator.models import EvaluationResult
from src.utils.helpers import Helpers


def cmd_task(platform: TrainingPlatform, day: int):
    """View task"""
    task = platform.get_task(day)
    if not task:
        Helpers.print_error(f"Day {day} task not found")
        return
    
    phase_info = Helpers.get_phase_info(day)
    
    # 1. 今日主题
    print(f"Day {day}: {task.title}")
    print(f"Phase: {phase_info['name']}")
    print(f"Goal: {task.goal}")
    # 2. 预计时间
    if getattr(task, "estimated_minutes", 0):
        print(f"Estimated: ~{task.estimated_minutes} minutes")
    print(f"\nDescription:\n{task.description}")
    # 3. 前置知识
    prerequisites = getattr(task, "prerequisites", None) or []
    if prerequisites:
        print(f"\nPrerequisites:")
        for p in prerequisites:
            print(f"  - {p}")
    # 4. 今天需要学习
    learn = getattr(task, "learn", None) or []
    if learn:
        print(f"\n今天需要学习 (learn):")
        for item in learn:
            print(f"  - {item}")
    # 5. Required API（签名+行为约定，不含实现）
    required_api = getattr(task, "required_api", None) or []
    if required_api:
        print(f"\nRequired API:")
        for api in required_api:
            if isinstance(api, dict):
                print(f"  {api.get('signature', '')}")
                desc = api.get("description", "")
                if desc:
                    print(f"    - {desc}")
            else:
                print(f"  {api}")
    # 6. 核心任务
    core_task = getattr(task, "core_task", "") or task.task
    print(f"\n核心任务:\n{core_task}")
    # 7. Mastery
    mastery = getattr(task, "mastery", None) or []
    if mastery:
        print(f"\n掌握标准 (mastery):")
        for item in mastery:
            print(f"  - {item}")
    # 8. Hints（支持分级）
    hint_levels = getattr(task, "hint_levels", None) or {}
    if hint_levels:
        print(f"\nHints (卡住时按级查看):")
        for level in sorted(hint_levels.keys()):
            for h in hint_levels[level]:
                print(f"  [L{level}] {h}")
    elif task.hints:
        print(f"\nHints:")
        for h in task.hints:
            print(f"  - {h}")
    # 9. Optional Challenge
    challenge = getattr(task, "optional_challenge", "")
    if challenge:
        print(f"\n可选挑战 (challenge失败不影响当天通过):\n{challenge}")
    # 测试函数名属于系统内部细节，不再向学习者展示


def cmd_submit(platform: TrainingPlatform, day: int, file_path: str):
    """Submit code"""
    submission_path = Path(file_path)
    
    if not submission_path.exists():
        Helpers.print_error(f"File not found: {file_path}")
        return
    
    Helpers.print_info(f"Evaluating Day {day} submission...")
    result = platform.evaluate_submission(day, submission_path)
    
    platform.save_progress(result)
    
    print(f"\n{'='*50}")
    print(f"Day {day} Evaluation Result")
    print(f"{'='*50}")
    print(f"Syntax valid: {result.syntax_valid}")
    print(f"Execution success: {result.execution_success}")
    print(f"Timeout: {result.timeout}")
    print(f"Tests: {result.tests_passed}/{result.tests_total} passed")
    print(f"Test score: {result.test_score:.1f}")
    print(f"AI score: {result.ai_score:.1f}" if result.ai_score is not None else "AI score: N/A")
    print(f"Final score: {result.final_score:.1f}")
    
    if result.ai_review:
        sections = [
            ("Strengths", "strengths", "+"),
            ("Issues", "issues", "-"),
            ("Knowledge Gaps", "knowledge_gaps", "?"),
            ("Improvement", "improvement", "*"),
            ("Next Learning", "next_learning", ">"),
        ]
        for title, key, mark in sections:
            items = result.ai_review.get(key) or []
            if items:
                print(f"\n{title}:")
                for item in items:
                    print(f"  {mark} {item}")


def cmd_progress(platform: TrainingPlatform):
    """View progress"""
    stats = platform.get_statistics()
    
    print(f"Attempted days: {stats.get('attempted_days', 0)}/40")
    print(f"Completed days: {stats.get('completed_days', 0)}/40 (score>=60)")
    print(f"Total submissions: {stats.get('total_submissions', 0)}")
    print(f"Completion rate: {stats.get('completion_rate', 0):.1f}%")
    print(f"Average score: {stats.get('average_score', 0):.1f}")
    print(f"Max score: {stats.get('max_score', 0):.1f}")


def cmd_report(platform: TrainingPlatform):
    """Generate report"""
    progress_list = platform.get_all_progress()
    stats = platform.get_statistics()
    
    if not progress_list:
        print("No progress data yet.")
        return
    
    print(f"\n{'='*50}")
    print(f"Learning Report")
    print(f"{'='*50}")
    print(f"Attempted: {stats.get('attempted_days', 0)}/40")
    print(f"Completed: {stats.get('completed_days', 0)}/40 (score>=60)")
    print(f"Avg score: {stats.get('average_score', 0):.1f}")
    print(f"Max score: {stats.get('max_score', 0):.1f}")
    
    print(f"\n{'Day':<6} {'Score':<10} {'Status'}")
    print("-"*30)
    for p in progress_list:
        status = "PASS" if p.score >= 60 else "FAIL"
        print(f"{p.day:<6} {p.score:<10.1f} {status}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="AI Engineer Training Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # task
    task_parser = subparsers.add_parser("task", help="View task")
    task_parser.add_argument("day", type=int, help="Day number (1-40)")
    
    # submit
    submit_parser = subparsers.add_parser("submit", help="Submit code")
    submit_parser.add_argument("day", type=int, help="Day number (1-40)")
    submit_parser.add_argument("file", help="Path to answer.py")
    
    # progress
    subparsers.add_parser("progress", help="View progress")
    
    # report
    subparsers.add_parser("report", help="Generate report")
    
    # interactive
    subparsers.add_parser("start", help="Start interactive mode")
    
    args = parser.parse_args()
    
    platform = TrainingPlatform()
    
    if args.command == "task":
        cmd_task(platform, args.day)
    elif args.command == "submit":
        cmd_submit(platform, args.day, args.file)
    elif args.command == "progress":
        cmd_progress(platform)
    elif args.command == "report":
        cmd_report(platform)
    elif args.command == "start":
        _interactive_mode(platform)
    else:
        parser.print_help()


def _interactive_mode(platform: TrainingPlatform):
    """Interactive mode"""
    while True:
        print(f"\n{'='*50}")
        print(f"AI Engineer Training - Day {platform.current_day}")
        print(f"{'='*50}")
        print("1. View task")
        print("2. Submit code")
        print("3. View progress")
        print("4. Set day")
        print("0. Exit")
        
        choice = input("\nChoice: ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            cmd_task(platform, platform.current_day)
        elif choice == "2":
            submit_dir = Path("submissions") / f"day{platform.current_day:02d}"
            file_path = input(f"File path (default: {submit_dir}/answer.py): ").strip()
            if not file_path:
                file_path = str(submit_dir / "answer.py")
            cmd_submit(platform, platform.current_day, file_path)
        elif choice == "3":
            cmd_progress(platform)
        elif choice == "4":
            try:
                day = int(input("Day (1-40): ").strip())
                if 1 <= day <= 40:
                    platform.current_day = day
                    Helpers.print_success(f"Set to Day {day}")
                else:
                    Helpers.print_error("Day must be 1-40")
            except ValueError:
                Helpers.print_error("Invalid number")


if __name__ == "__main__":
    main()
