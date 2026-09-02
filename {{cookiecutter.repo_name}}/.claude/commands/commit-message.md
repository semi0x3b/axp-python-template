---
description: Gitmoji 규칙으로 커밋 후 작업 브랜치를 develop에 반영(push, non-ff면 무체크아웃 머지). model/마이그레이션은 migration 브랜치로 분리
allowed-tools: Bash(git:*), Bash(alembic:*), Bash(poetry run alembic:*), Bash(grep:*)
---

## Context

- Current git status: !`git status`
- Current branch: !`git rev-parse --abbrev-ref HEAD`
- Staged changes (stat): !`git diff --cached --stat`
- Unstaged changes (stat): !`git diff --stat`
- Untracked files: !`git ls-files --others --exclude-standard`
- Recent commits (for style reference): !`git log --oneline -10`

> 커밋 메시지 작성에 필요한 파일만 `git diff -- <파일>` / `git diff --cached -- <파일>` 로 선별해서 읽는다(전체 diff 덤프 금지).

## Gitmoji Convention

`<emoji> <TAG>: <제목>` + (선택) 빈 줄 + 본문. 아래 표만 사용한다(외부 문서 참조 없음).

| Emoji | TAG | 설명 |
|---|---|---|
| ✨ | FEAT | 새 기능 |
| 🐛 | FIX | 버그 수정 |
| 🚑 | HOTFIX | 긴급 핫픽스 |
| 🔨 | UPDATE | 코드 수정 |
| 📝 | DOCS | 문서 변경 |
| 🎨 | STYLE | 코드 스타일/구조 |
| ♻️ | REFACTOR | 리팩토링 |
| 🧪 | TEST | 테스트 추가/수정 |
| ⚡ | PERF | 성능 개선 |
| 👷 | CI | CI/CD 변경 |
| 🔒 | SECURITY | 보안 수정 |
| 🚀 | DEPLOY | 배포 관련 |
| 🔥 | REMOVE | 코드/파일 제거 |
| 🔀 | MERGE | 브랜치 병합 |
| 🎉 | INIT | 프로젝트 초기화 |
| 📦 | DEPS | 의존성 변경 |
| ⬆️ | CHORE | 빌드/설정 변경 |
| 🚚 | MOVE | 파일 이동/이름 변경 |
| 🗃️ | MIGRATION | DB 마이그레이션 |

## Commit Message Format

```
<emoji> <TAG>: <제목>

[본문 - 선택사항]
```

**제목 규칙**: 한글 / 마침표 없음 / 50자 이내 / 명령형 / TAG 대문자.
**본문 규칙**(선택): 제목과 빈 줄 분리 / 72자 줄바꿈 / "무엇을·왜".

## 안전장치 (모든 Case 공통, 위반 시 즉시 중단)

1. **현재 브랜치가 `main`/`master`이거나 detached HEAD(브랜치 아님)면 즉시 중단**하고 "작업 브랜치에서 먼저 작업하세요"라고 알린다. 어떤 커밋·push도 하지 않는다.
2. **현재 브랜치가 `release/*` 또는 `hotfix/*`이면**, develop 반영 단계 진입 전에 "이 브랜치를 develop에 반영하는 게 맞는지" 사용자에게 1회 확인한다. (feature/bugfix 등 일반 브랜치는 무확인 자동 진행.)
3. **develop을 checkout하지 않고, 작업 브랜치를 rebase하지도 않는다.** develop 반영은 fetch + `git push origin HEAD:develop`, non-ff면 무체크아웃 머지(아래 공통 절차 4). → 작업 브랜치에 develop이 절대 섞이지 않으므로, 이후 main에 올려도 develop이 딸려가지 않는다.
4. **충돌 시 임의 해결 금지.** 충돌 파일별로 양쪽(ours/theirs) 변경을 사용자에게 보여주고 선택받는다. 확인 전 다음 단계로 가지 않는다.
5. 커밋 메시지에 **`Co-Authored-By` 라인을 절대 포함하지 않는다.**
6. **스테이징 여부를 묻지 않고** 자동 진행한다(논리적으로 분리되는 변경이면 별도 커밋을 제안만 한다).

## Step 0: 컨벤션 사전 검사

변경 파일 중 컨벤션 점검 대상(`_repo.py` / `_usecase.py` 등)이 있으면 해당 파일만 `check-convention` 규칙으로 점검·수정 후 커밋 대상에 포함한다. 애매하면(JOIN 쿼리 등) 사용자에게 확인. 대상 없으면 건너뜀.

### 에러코드 중복 가드

변경 파일에 `app/core/enum/response_message.py`가 포함되면, 커밋 전 중복 `code` 값을 검사한다.

```bash
grep -oE '"code": "ERR-[0-9A-Za-z\-]+"' app/core/enum/response_message.py | sort | uniq -d
```

- 출력이 있으면(같은 ERR 코드를 둘 이상이 공유) **커밋 중단** + 중복 목록 보고.
- 해소 원칙: 섹션 주석상 그 번호대를 소유한 정본 상수는 유지, **침입한 상수만** 같은 섹션의 미사용(free) 코드로 이동. app은 전부 상수(`ErrorResponseMessage.X`) 경유라 dict `code` 값 변경만으로 전파. 테스트가 옛 코드를 단언하는지 `grep -rn "ERR-XXXX" tests/` 확인 후 이동.
- 출력 없으면 통과.

## Your Task

`git status` / `git diff --name-only` / `git ls-files --others --exclude-standard` 로 변경 파일을 파악한다.

- staged/unstaged/untracked가 **모두 없으면(작업 폴더 깨끗)** → **Case C**.
- 변경에 **model(`app/model/`)** 또는 **마이그레이션(`migrations/versions/`)** 이 포함되면 → **Case A**.
- 그 외 변경만 있으면 → **Case B**.

원래 브랜치를 변수로 기억한다: `ORIG_BRANCH=$(git rev-parse --abbrev-ref HEAD)`.

### Case A: model/마이그레이션 포함

model + migration 파일은 **별도 `migration` 브랜치에 커밋·push**하고, 나머지 변경은 현재 작업 브랜치에 커밋한다.

> **선행(최초 1회): `migration` 브랜치 부트스트랩.** 신규 repo는 공유 `migration` 브랜치가 아직 없다. `git ls-remote --heads origin migration` 결과가 비어 있으면 develop 기준으로 생성한다(checkout 없음):
>   `git fetch origin develop`
>   `git push origin origin/develop:refs/heads/migration --no-verify`
> 이미 origin/migration이 있으면 이 블록을 건너뛰고 아래 step 3로 진행한다.

1. **나머지(model/migration 제외)를 현재 브랜치에 커밋**
   - `app/model/` · `migrations/versions/` **이외** 변경 파일만 `git add` → Gitmoji 태그 선택 → `git commit`.
   - (model/migration 외 변경이 없으면 이 단계 건너뜀.)
2. **model + migration만 stash로 분리**
   - `git stash push -u -m "tmp-migration-files" -- app/model/ migrations/versions/`
   - `git status` 로 작업 트리에서 빠졌는지 확인.
3. **`migration` 브랜치로 이동 + 최신화 + 커밋 + push**
   - `git fetch origin migration`
   - `git checkout migration` — **"already checked out" 오류면 중단**: migration 브랜치를 다른 워크트리가 점유 중이다. `git worktree list` 결과를 사용자에게 보여주고 판단을 받는다(stash는 `git stash list`의 `tmp-migration-files` 항목으로 남아 있음).
   - `git pull --ff-only origin migration` — **실패 시 중단**하고 사용자에게 알린다. (복구: `git checkout $ORIG_BRANCH && git stash pop` 으로 원상복귀 후 사용자 판단.)
   - `git stash pop` — 여러 stash가 있으면 `git stash list`에서 `tmp-migration-files` 항목의 인덱스를 지정해 pop한다. **충돌 시 중단**하고 충돌 파일을 사용자에게 보여준다(임의 해결 금지). 복구는 `git checkout --merge`로 해결하거나, 사용자가 **직접** `git reset --hard` 후 `git checkout $ORIG_BRANCH && git stash pop` 으로 원복하도록 안내한다(에이전트가 reset --hard를 실행하지 않는다).
   - `git add app/model/ migrations/versions/`
   - 마이그레이션 파일이 포함되면 **단일 head 검증**: `alembic heads` 출력이 head **1개**인지 확인 (bare `alembic`이 PATH에 없으면 `poetry run alembic heads`). 2개 이상(multiple heads)이면 중단하고 사용자에게 알린다(merge revision 필요).
   - Gitmoji 규칙으로 커밋: `🗃️ MIGRATION: <설명>` (model만이고 마이그레이션이 없으면 `🔨 UPDATE` 등 적절히).
   - `git push --no-verify origin migration` — migration 브랜치 push는 pre-push hook 스킵.
4. **원래 브랜치 복귀 + migration 머지백 + push**
   - `git checkout $ORIG_BRANCH`
   - `git merge migration --no-ff` — model/migration 커밋을 작업 브랜치에서도 쓸 수 있게 머지. **이 머지백은 squash 하지 않는다**(공유 `migration` 브랜치 이력 보존). 충돌 시 안전장치 4 적용. 메시지 기본값: `🔀 MERGE: migration 브랜치 병합`.
   - `git push origin $ORIG_BRANCH`
5. **develop 반영** → 아래 공통 절차 수행.

### Case B: model/마이그레이션 없음

1. 변경을 논리 단위로 분석해 Gitmoji 태그 선택(분리되면 별도 커밋 제안).
2. staged가 없으면 `git add -A` 후 `git commit`(스테이징 자동).
3. `git push origin $ORIG_BRANCH`
4. **develop 반영** → 아래 공통 절차 수행.

### Case C: 변경사항 없음 (작업 폴더 깨끗)

커밋 없이 push + develop 반영만 진행한다.

1. `git push origin $ORIG_BRANCH`
2. **develop 반영** → 아래 공통 절차 수행.

---

### develop 반영 공통 절차 (Case A/B/C 공통)

> **develop을 checkout하지 않고, 작업 브랜치를 rebase·merge로 변형하지도 않는다.** 작업 브랜치는 어떤 경우에도 그대로다 — 이후 main에 올려도 develop이 딸려가지 않는다.

1. (안전장치 2 — release/hotfix면 사용자 확인 먼저.)
2. `git fetch origin develop` — origin/develop 최신화(로컬 develop 브랜치·작업 트리는 건드리지 않음).
3. `git push origin HEAD:develop` — fast-forward로 성공하면 여기서 끝.
4. **non-fast-forward로 거부되면**(develop에 내 브랜치에 없는 커밋이 있는 정상 상황) — checkout 없이 머지 커밋을 만들어 push한다. **각 명령은 개별 실행한다** — 파이프·`xargs`·`$(...)`로 한 줄에 묶으면 `Bash(git:*)` 자동 허용을 벗어나 권한 차단된다. 앞 명령 출력(트리/커밋 OID)을 읽어 다음 명령 인자에 그대로 넣는다:
   - `git merge-tree --write-tree origin/develop HEAD`
     - **exit 0(충돌 없음)**: 출력 첫 줄이 머지 결과 트리 OID.
     - **exit 1(충돌)**: **중단.** 출력의 충돌 파일 목록을 사용자에게 제시한다(임의 해결 금지).
   - `git commit-tree <트리OID> -p origin/develop -p HEAD -m "🔀 MERGE: $ORIG_BRANCH → develop"` — 본문에 `git log origin/develop..HEAD --oneline` 핵심 요약을 넣어도 좋다.
   - `git push origin <새커밋OID>:develop`
   - 이 push도 거부되면(그새 develop이 또 전진) 2번부터 **1회만** 재시도, 재실패 시 사용자에게 보고.
5. 작업 브랜치는 그대로다(checkout·merge·rebase 없음).

## 보고
- 만든 커밋(해시/메시지), Case A면 `migration` 브랜치 커밋·push 여부 및 `alembic heads` 결과, develop 반영 방식(ff push / 무체크아웃 머지 커밋 해시).
- 마이그레이션 `revision/upgrade` 실행은 사용자가 직접 한다(이 커맨드는 생성/실행하지 않음).
