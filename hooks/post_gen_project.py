"""cookiecutter 프로젝트 생성 후 실행되는 훅."""

import os
import shutil
import subprocess
import sys
from pathlib import Path


OUTPUT_PARENT = "{{cookiecutter.output_parent}}"


def relocate(current: Path) -> Path:
    """output_parent가 '.'가 아니면 생성된 프로젝트를 해당 경로로 이동한다."""
    if not OUTPUT_PARENT or OUTPUT_PARENT == ".":
        return current

    target_parent = Path(OUTPUT_PARENT).expanduser().resolve()
    target = target_parent / current.name

    if target == current:
        return current

    if target.exists():
        print(f"⚠️  {target} 이미 존재. 이동 취소. 생성 위치: {current}", file=sys.stderr)
        return current

    target_parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(current), str(target))
    os.chdir(target)
    return target


def register_version_merge_driver(project_dir: Path) -> None:
    """.gitattributes 의 merge=version-aware 가 실제로 동작하도록 로컬 git config 에 등록한다.

    드라이버 정의는 .gitattributes 로 전파되지 않는다. 등록하지 않아도 기본 text 머지로
    폴백하므로 실패해도 치명적이지 않다.
    """
    driver = ".github/merge-drivers/version-merge.py %O %A %B %L %P"
    try:
        subprocess.run(["git", "config", "merge.version-aware.name", "version-aware merge"], cwd=project_dir, check=True)
        subprocess.run(["git", "config", "merge.version-aware.driver", driver], cwd=project_dir, check=True)
        print("✅ version-aware 머지 드라이버 등록 완료")
    except Exception as e:
        print(f"⚠️  머지 드라이버 등록 실패(무시 가능): {e}", file=sys.stderr)


def main() -> None:
    project_dir = relocate(Path.cwd())

    try:
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=project_dir, check=True)
        print(f"\n✅ git 저장소 초기화 완료 (main branch)")
    except Exception as e:
        print(f"⚠️  git init 실패: {e}", file=sys.stderr)

    register_version_merge_driver(project_dir)

    print(
        f"""
🎉 프로젝트 생성 완료: {project_dir}

다음 단계:
  cd {project_dir}
  cp .env.example .env
  poetry install
  poetry run pre-commit install && poetry run pre-commit install --hook-type pre-push
  make up                   # PostgreSQL + Redis 기동
  make revision MSG="init"  # 초기 migration 생성
  make migrate              # migration 적용
  make dev                  # 개발 서버 기동

  curl http://localhost:8000/healthz
"""
    )


if __name__ == "__main__":
    main()
