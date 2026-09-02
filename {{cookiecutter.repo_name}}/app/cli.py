"""CLI 엔트리포인트.

Job 수동 실행 명령을 제공한다.

Usage:
    python -m app.cli job run <name>
    python -m app.cli job list
"""

import argparse
import asyncio
import sys

from app.core.logger import configure_logger, get_logger

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """CLI argument parser를 구성한다."""
    parser = argparse.ArgumentParser(prog="python -m app", description="{{cookiecutter.project_name}} Job CLI")
    subparsers = parser.add_subparsers(dest="command")

    # --- job ---
    job_parser = subparsers.add_parser("job", help="Job 실행")
    job_sub = job_parser.add_subparsers(dest="action")

    run_parser = job_sub.add_parser("run", help="Job 1회 수동 실행")
    run_parser.add_argument("name", help="Job 이름 (e.g., expire-badges)")

    job_sub.add_parser("list", help="등록된 Job 목록 조회")

    return parser


async def cmd_job_run(name: str) -> None:
    """지정된 Job을 1회 실행한다."""
    from app.domain.job.scheduler.runner import execute

    configure_logger()
    await execute(name)


def cmd_job_list() -> None:
    """등록된 Job 목록을 출력한다."""
    from app.domain.job.scheduler.runner import JOB_REGISTRY

    if not JOB_REGISTRY:
        print("등록된 Job이 없습니다.")
        return

    print(f"{'Name':<25} {'Func':<70}")
    print("-" * 95)
    for name, config in JOB_REGISTRY.items():
        print(f"{name:<25} {config['func']:<70}")


def main() -> None:
    """CLI 메인 진입점."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "job":
        if args.action == "run":
            asyncio.run(cmd_job_run(args.name))
        elif args.action == "list":
            cmd_job_list()
        else:
            parser.parse_args(["job", "--help"])
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
