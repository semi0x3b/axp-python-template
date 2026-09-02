---
description: 커밋만 수행 (push/merge 없음)
allowed-tools: Bash(git:*)
---

## Context

- Current git status: !`git status`
- Staged changes: !`git diff --cached`
- Unstaged changes (if any): !`git diff`
- Recent commits (for style reference): !`git log --oneline -10`

## Gitmoji Convention
커밋 작성 시 다음 Gitmoji 규칙을 따릅니다:

| Emoji | Tag | Description | Example |
|-------|-----|-------------|---------|
| ✨ | FEAT | 새로운 기능 추가 | `✨ FEAT: 사용자 인증 기능 추가` |
| 🐛 | FIX | 버그 수정 | `🐛 FIX: 로그인 실패 문제 해결` |
| 🚑 | HOTFIX | 긴급 핫픽스 | `🚑 HOTFIX: 서버 장애 긴급 패치` |
| 🔨 | UPDATE | 코드 수정 | `🔨 UPDATE: 응답 메시지 형식 수정` |
| 📝 | DOCS | 문서 변경 | `📝 DOCS: API 문서 업데이트` |
| 🎨 | STYLE | 코드 스타일/구조 | `🎨 STYLE: 코드 포맷팅 적용` |
| ♻️ | REFACTOR | 코드 리팩토링 | `♻️ REFACTOR: 사용자 서비스 리팩토링` |
| 🧪 | TEST | 테스트 추가/수정 | `🧪 TEST: 사용자 API 테스트 추가` |
| ⚡ | PERF | 성능 개선 | `⚡ PERF: 쿼리 성능 최적화` |
| 👷 | CI | CI/CD 변경 | `👷 CI: GitHub Actions 설정 추가` |
| 🔒 | SECURITY | 보안 수정 | `🔒 SECURITY: XSS 취약점 패치` |
| 🚀 | DEPLOY | 배포 관련 | `🚀 DEPLOY: v1.0.0 배포` |
| 🔥 | REMOVE | 코드/파일 제거 | `🔥 REMOVE: 사용하지 않는 컴포넌트 제거` |
| 🔀 | MERGE | 브랜치 병합 | `🔀 MERGE: feature/auth를 develop에 병합` |
| 🎉 | INIT | 프로젝트 초기화 | `🎉 INIT: 프로젝트 초기 설정` |
| 📦 | DEPS | 의존성 변경 | `📦 DEPS: SQLAlchemy 버전 업그레이드` |
| ⬆️ | CHORE | 빌드/설정 변경 | `⬆️ CHORE: 빌드 스크립트 수정` |
| 🚚 | MOVE | 파일 이동/이름 변경 | `🚚 MOVE: 유틸 함수 위치 변경` |

## Commit Message Format

```
<emoji> <TAG>: <제목>

[본문 - 선택사항]
```

## Rules

**Title Rules**:
- 한글로 작성
- 마침표 사용 안 함
- 50자 이내
- 명령형 사용 ("추가", "수정", "변경")

**Body Rules** (선택):
- 제목과 본문 사이 빈 줄 삽입
- 72자에서 줄바꿈
- "무엇을", "왜" 했는지 설명

## Your Task

1. 변경 사항을 분석하여 적절한 Gitmoji 태그 선택
2. 변경 유형에 맞는 커밋 메시지 생성
3. staged 변경사항이 없으면 `git add -A`로 모든 변경사항 스테이징 후 커밋
4. `git commit` 실행
5. **push/merge 하지 않음** — 커밋만 수행

**중요**:
- `Co-Authored-By` 라인은 절대 포함하지 마세요
- 여러 변경사항이 논리적으로 분리되면 별도 커밋 제안
- 사용자에게 스테이징 여부를 묻지 말고 자동으로 진행
