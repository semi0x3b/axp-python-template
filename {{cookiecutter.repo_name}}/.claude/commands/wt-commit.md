# wt-commit — 워크트리 커밋 후 분기원 브랜치 머지

워크트리(git worktree)에서 작업한 변경을 커밋한 뒤, **분기원(상위) 브랜치로 머지**까지 수행한다.
상위 브랜치 push 는 하지 않는다 (로컬까지만). model/마이그레이션만 예외적으로 `migration` 브랜치에 push 한다.

> 일반 작업 브랜치(워크트리 아님)에서 develop 까지 푸시·병합하려면 `commit-message` 를 사용한다.
> 이 커맨드는 **워크트리 → 분기원 브랜치** 로컬 병합 전용이다.

---

## Gitmoji Convention

| Emoji | Tag | Description |
|-------|-----|-------------|
| ✨ | FEAT | 새로운 기능 추가 |
| 🐛 | FIX | 버그 수정 |
| 🚑 | HOTFIX | 긴급 핫픽스 |
| 🔨 | UPDATE | 코드 수정 |
| 📝 | DOCS | 문서 변경 |
| 🎨 | STYLE | 코드 스타일/구조 |
| ♻️ | REFACTOR | 코드 리팩토링 |
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

**메시지 형식**: `<emoji> <TAG>: <제목>` + (선택) 빈 줄 + 본문.
**제목 규칙**: 한글, 마침표 없음, 50자 이내, 명령형. **`Co-Authored-By` 라인 절대 금지.**

---

## Step 0: 워크트리 검증 + 분기원 브랜치 감지

1. **현재 브랜치 확인**: `W=$(git rev-parse --abbrev-ref HEAD)`
2. **워크트리 여부 확인**: `git rev-parse --git-common-dir` 와 `--git-dir` 가 다르면 linked worktree.
   - 메인 워크트리(둘이 같음)에서 실행됐으면 **중단**하고 사용자에게 알린다 ("이 커맨드는 워크트리 전용. 일반 브랜치는 `commit-message` 사용").
3. **분기원 `P` 자동 감지** (순서대로 시도):
   - (1) reflog: `git reflog show "$W" 2>/dev/null` 의 최초 `branch: Created from <P>` 항목에서 `<P>` 추출.
   - (2) 실패 시 merge-base 추정: 로컬 브랜치(`W`·detached 제외) 각각에 대해 `git merge-base --is-ancestor` / `git rev-list --count <mb>..<B>` 를 비교해 `W` 와 공통 조상이 가장 가까운 브랜치를 후보로 삼는다.
   - (3) 후보가 0개이거나 2개 이상으로 모호하면 **중단**하고 사용자에게 분기원 브랜치를 직접 묻는다 (오머지 방지).
4. `P == W` 이거나 `P` 가 존재하지 않으면 **중단**.

원래 작업 위치(워크트리 경로)와 `W`, `P` 를 변수로 기억한다.

---

## Step 1: 컨벤션 사전 검사

변경 파일에 `_repo.py` / `_usecase.py` 가 있으면 해당 파일만 `check-convention.md` 규칙으로 검사한다.
- 위반 발견 시 자동 수정 후 커밋 대상에 포함.
- JOIN 쿼리 등 애매한 경우 사용자에게 확인.
- 대상 없으면 건너뜀.

---

## Step 2: 커밋

변경사항 유무 확인. staged/unstaged/untracked 모두 없으면 커밋 없이 **Step 3(머지)** 로 진행.

`git diff --name-only` + `git ls-files --others --exclude-standard` 로 model 파일(`app/model/`)·마이그레이션(`migrations/versions/`) 포함 여부를 판단한다.

### Case A: model/마이그레이션 포함

model+migration 은 **`migration` 브랜치에 커밋·push**, 나머지는 워크트리 브랜치 `W` 에 커밋한다.

1. **나머지(model/migration 제외)를 `W` 에 커밋**:
   - `git add <model/migration 제외한 변경 파일들>`
   - Gitmoji 태그 선택 후 `git commit`
   - (그 외 변경이 없으면 건너뜀)
2. **model+migration 분리**: `git stash push -u -m "tmp-migration-files" -- app/model/ migrations/versions/` → `git status` 로 작업 트리에서 빠졌는지 확인.
3. **`migration` 브랜치 작업** — `migration` 이 다른 워크트리에 체크아웃돼 있으면 그 경로에서 `-C` 로 수행, 아니면 현재 워크트리에서 체크아웃:
   - `git fetch origin migration`
   - 체크아웃(또는 `-C <migration-worktree>`), `git pull --ff-only origin migration` (실패 시 알리고 중단)
   - **현재 head 기억**: `PREV_HEAD=$(alembic heads | awk '{print $1}')` (bare `alembic`이 PATH에 없으면 `poetry run alembic`). head가 1개가 아니면 이미 갈라진 상태이니 중단하고 알린다.
   - `git stash pop` (충돌 시 알리고 중단)
   - **선형화 (멀티헤드 금지)**: 마이그레이션 포함 시 복원된 **새 리비전**의 `down_revision`을 `$PREV_HEAD`(migration 브랜치의 현재 head)로 재지정해 체인을 잇는다. `down_revision = "<옛값>"` → `down_revision = "<$PREV_HEAD 값>"`. 새 리비전이 여러 개면 생성 순서대로 사슬로 연결하고 최하단만 `$PREV_HEAD`에 붙인다.
   - `git add app/model/ migrations/versions/` (선형화로 수정한 파일 포함)
   - **단일 head 검증**: `alembic heads`가 정확히 1개인지 확인. 선형화 후에도 2개 이상이면 자동 해결하지 말고 중단해 알린다.
   - `🗃️ MIGRATION: <설명>` 커밋
   - `git push --no-verify origin migration` (migration 브랜치 push 는 pre-push hook 스킵)
4. **`W` 로 복귀** 후 `git merge migration --no-ff` 로 방금 model/migration 커밋을 `W` 에도 반영 (충돌 시 임의해결 금지, 사용자에게 양쪽 제시).

### Case B: model/마이그레이션 없음

- staged 없으면 `git add -A`
- Gitmoji 태그 선택 후 `git commit`

> **push 정책**: `W` 는 push 하지 않는다. push 하는 것은 `migration` 브랜치뿐이다.

---

## Step 3: 분기원 브랜치 `P` 로 머지 (push 안 함)

`P` 가 체크아웃된 워크트리를 찾는다: `git worktree list --porcelain` 에서 `branch refs/heads/<P>` 의 경로 `Xp`.

**분기원 `P` 병합은 일반 머지(`--no-ff`)로 수행한다.** squash 를 쓰지 않는 이유: squash 는 부모에 원본 히스토리 연결(parent 링크)을 남기지 않아 merge-base 가 전진하지 않고, 다음 wt-commit 때 이미 반영된 파일들이 "양쪽에서 새로 추가됨"으로 보여 **재충돌**한다. `--no-ff` 는 실제 머지 커밋으로 히스토리를 보존해 이 재충돌을 막는다. 머지 커밋 메시지: `🔀 MERGE: <W>를 <P>에 병합`.

- **`P` 가 워크트리 `Xp` 에 체크아웃됨**: `git -C "$Xp" merge --no-ff "$W" -m "🔀 MERGE: <W>를 <P>에 병합"`
  - `Xp` 에 uncommitted 변경이 있어 머지 불가하면 중단하고 사용자에게 알린다.
- **`P` 가 어디에도 체크아웃 안 됨**: 현재 워크트리에서 `git checkout "$P" && git merge --no-ff "$W" -m "🔀 MERGE: <W>를 <P>에 병합" && git checkout "$W"` (W 커밋은 브랜치 W 에 안전하게 보존됨).

충돌 발생 시: **임의로 해결하지 않고** 충돌 파일별 양쪽 변경을 사용자에게 보여준 뒤 선택받는다.

**`P` 는 push 하지 않는다.** (로컬 병합까지만)

---

## Step 4: 보고

- `W` 커밋 결과 (해시/메시지)
- `migration` 브랜치 커밋·push 여부 (Case A인 경우)
- `P` 머지 결과 (FF/merge commit/충돌)
- 후속 안내: `P` push 는 수동, 마이그레이션 `upgrade head` 는 사용자가 직접 실행

---

## 주의사항

- `Co-Authored-By` 라인 절대 금지.
- 상위 브랜치 `P` push 금지 (로컬까지만). `migration` 브랜치만 push.
- 충돌은 임의 해결 금지 — 사용자에게 양쪽 제시 후 선택.
- 분기원 `P` 감지가 모호하면 진행하지 말고 사용자에게 확인 (오머지 방지).
- 메인 워크트리에서 실행 시 중단 (이 커맨드는 워크트리 전용).
