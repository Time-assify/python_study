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
    
    print(f"Day {day}: {task.title}")
    print(f"Phase: {phase_info['name']}")
    print(f"Goal: {task.goal}")
    print(f"\nDescription:\n{task.description}")
    
    if task.tests:
        print(f"\nTests: {', '.join(task.tests)}")
    
    if task.hints:
        print(f"\nHints:")
        for h in task.hints:
            print(f"  - {h}")


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
        if result.ai_review.get("strengths"):
            print(f"\nStrengths:")
            for s in result.ai_review["strengths"]:
                print(f"  + {s}")
        if result.ai_review.get("bugs"):
            print(f"\nBugs:")
            for b in result.ai_review["bugs"]:
                print(f"  - {b}")
        if result.ai_review.get("suggestions"):
            print(f"\nSuggestions:")
            for s in result.ai_review["suggestions"]:
                print(f"  * {s}")


def cmd_progress(platform: TrainingPlatform):
    """View progress"""
    stats = platform.get_statistics()
    
    print(f"\nProgress: {stats.get('completed_days', 0)}/40 days")
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
    print(f"Completed: {stats.get('completed_days', 0)}/40")
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
