#!/usr/bin/env bash
# main → <target> 자동 동기화가 충돌했을 때, 각 충돌 파일이 어떤 성격인지 분류한다.
# 해결은 하지 않는다 — 사람이 어디부터 봐야 할지 판단을 돕는 것이 목적이다.
#
# usage: classify-sync-conflicts.sh <target-branch> <파일목록 파일>
#   파일목록: `git diff --name-only --diff-filter=U` 결과
#
# 분류 기준
#   🔁 중복 커밋  : main 과 target 의 해당 파일 최종 내용이 동일. 같은 수정이 양쪽에
#                   따로 커밋되어 git 이 별개 변경으로 보는 경우. 어느 쪽을 택해도 결과 동일.
#   ⚠️ 실제 차이  : 내용이 다르다. 양쪽이 서로 다른 결정을 했을 수 있어 사람 판단 필요.
set -u

TARGET="$1"
FILE_LIST="$2"

blob_of() { # <ref> <path> — 없으면 빈 문자열
  git rev-parse --quiet --verify "$1:$2" 2>/dev/null || true
}

dup=0
real=0
dup_lines=""
real_lines=""

while IFS= read -r f; do
  [ -z "$f" ] && continue
  a="$(blob_of "origin/main" "$f")"
  b="$(blob_of "origin/${TARGET}" "$f")"

  if [ -n "$a" ] && [ "$a" = "$b" ]; then
    dup=$((dup + 1))
    dup_lines="${dup_lines}- \`${f}\`
"
  else
    real=$((real + 1))
    stat="$(git diff --numstat "origin/${TARGET}" origin/main -- "$f" 2>/dev/null | awk '{print "+"$1" -"$2}')"
    [ -z "$stat" ] && stat="한쪽에만 존재"
    mc="$(git log -1 --format='%h %s' origin/main -- "$f" 2>/dev/null)"
    tc="$(git log -1 --format='%h %s' "origin/${TARGET}" -- "$f" 2>/dev/null)"
    real_lines="${real_lines}- \`${f}\` (${stat})
  - main: ${mc:-(변경 없음)}
  - ${TARGET}: ${tc:-(변경 없음)}
"
  fi
done < "$FILE_LIST"

echo "### 충돌 파일 분류"
echo
echo "판단 필요 **${real}건** / 중복 커밋 **${dup}건**"
echo

if [ "$real" -gt 0 ]; then
  echo "#### ⚠️ 판단 필요 — 양쪽 내용이 다릅니다"
  echo
  echo "서로 다른 결정을 했을 수 있습니다. 각 파일의 마지막 커밋을 보고 어느 쪽을 살릴지 정해주세요."
  echo
  printf '%s\n' "$real_lines"
fi

if [ "$dup" -gt 0 ]; then
  echo "#### 🔁 중복 커밋 — 양쪽 최종 내용이 동일합니다"
  echo
  echo "같은 수정이 main 과 \`${TARGET}\` 에 각각 커밋되어 git 이 별개 변경으로 본 경우입니다."
  echo "**어느 쪽을 택해도 결과가 같습니다.**"
  echo
  printf '%s\n' "$dup_lines"
fi

if [ -f .gitattributes ] && grep -q 'merge=version-aware' .gitattributes 2>/dev/null; then
  echo "#### ✅ 자동 처리 대상 (버전 줄)"
  echo
  echo "아래 파일의 버전 줄 충돌은 머지 드라이버가 자동 해결하므로 위 목록에 나타나지 않습니다."
  echo
  grep 'merge=version-aware' .gitattributes | awk '{print "- `" $1 "`"}'
  echo
fi
