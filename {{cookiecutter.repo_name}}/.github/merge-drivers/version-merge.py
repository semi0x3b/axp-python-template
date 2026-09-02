#!/usr/bin/env python3
"""버전 줄만 자동 해결하는 git merge driver.

main(배포) → develop(개발중) 자동 동기화 시 bumpversion 이 양쪽에서 각각 돌아
`__version__ = "1.6.3"` 같은 한 줄이 매 릴리스마다 충돌하는 문제를 없앤다.

동작:
  1. 평범한 3-way 머지를 먼저 시도한다.
  2. 충돌이 남으면, 충돌 블록의 모든 줄이 "버전 줄"인 경우에만 자동 해결한다.
     이때 어느 한쪽을 무조건 채택하지 않고 semver 가 더 높은 쪽을 고른다
     (main 이 hotfix 로 앞설 수도, develop 이 차기 버전으로 앞설 수도 있으므로).
  3. 버전 줄이 아닌 충돌이 하나라도 남으면 그대로 두고 실패(exit 1)한다.
     → 워크플로가 사람이 해결하도록 PR 을 연다.

git 사용법 (.gitattributes 의 merge=version-aware 와 짝):
    argv = %O(base) %A(ours) %B(theirs) %L(marker size) %P(path)
결과는 %A 에 쓴다.
"""

import re
import subprocess
import sys

# Python/ini 계열: `__version__ = "1.2.3"`, `version = "1.2.3"`, `current_version = 1.2.3`
# JSON 계열(package.json): `"version": "1.2.3",`
VERSION_LINE = re.compile(
    r"""^\s*(?:"""
    r"""(?:__version__|__base_version__|version|current_version)\s*=\s*["']?(?P<a>\d+\.\d+\.\d+)["']?\s*(?:\#.*)?"""
    r"""|"""
    r'''"version"\s*:\s*"(?P<b>\d+\.\d+\.\d+)"\s*,?'''
    r""")$"""
)


def semver(line):
    """버전 줄이면 (major, minor, patch) 튜플을, 아니면 None 을 반환."""
    m = VERSION_LINE.match(line)
    if not m:
        return None
    return tuple(int(x) for x in (m.group("a") or m.group("b")).split("."))


def resolve_block(ours, theirs):
    """충돌 블록 한 쌍을 해결한 줄 목록을 반환. 해결 불가면 None."""
    # 양쪽 모두 비어있지 않고, 모든 non-empty 줄이 버전 줄이어야 한다
    ours_v = [semver(l) for l in ours if l.strip()]
    theirs_v = [semver(l) for l in theirs if l.strip()]
    if not ours_v or not theirs_v:
        return None
    if any(v is None for v in ours_v + theirs_v):
        return None
    # 줄 수가 다르면 단순 버전 bump 가 아니므로 사람에게 넘긴다
    if len(ours) != len(theirs):
        return None
    # 더 높은 버전을 가진 쪽 전체를 채택
    return theirs if max(theirs_v) >= max(ours_v) else ours


def main():
    base, ours, theirs, marker = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

    # 1) 일반 3-way 머지. 성공하면 그대로 끝.
    rc = subprocess.call(
        [
            "git", "merge-file",
            "-L", "HEAD", "-L", "base", "-L", "main",
            "--marker-size", marker,
            ours, base, theirs,
        ]
    )
    if rc == 0:
        return 0
    if rc < 0:
        return 1  # merge-file 자체가 실패

    with open(ours, encoding="utf-8") as f:
        lines = f.read().splitlines(keepends=True)

    n = int(marker)
    start_re = re.compile(r"^<{%d} " % n)
    mid_re = re.compile(r"^={%d}\s*$" % n)
    end_re = re.compile(r"^>{%d} " % n)

    out, i, unresolved = [], 0, False
    while i < len(lines):
        if not start_re.match(lines[i]):
            out.append(lines[i])
            i += 1
            continue

        # 충돌 블록 파싱: <<<<<<< / ours / ======= / theirs / >>>>>>>
        j = i + 1
        ours_side = []
        while j < len(lines) and not mid_re.match(lines[j]):
            ours_side.append(lines[j])
            j += 1
        if j >= len(lines):  # 형태가 깨졌으면 손대지 않는다
            out.extend(lines[i:])
            unresolved = True
            break
        k = j + 1
        theirs_side = []
        while k < len(lines) and not end_re.match(lines[k]):
            theirs_side.append(lines[k])
            k += 1
        if k >= len(lines):
            out.extend(lines[i:])
            unresolved = True
            break

        resolved = resolve_block(ours_side, theirs_side)
        if resolved is None:
            out.extend(lines[i:k + 1])  # 충돌 마커째로 보존
            unresolved = True
        else:
            out.extend(resolved)
        i = k + 1

    with open(ours, "w", encoding="utf-8") as f:
        f.writelines(out)

    return 1 if unresolved else 0


if __name__ == "__main__":
    sys.exit(main())
