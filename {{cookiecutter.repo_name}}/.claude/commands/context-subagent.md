## 서브에이전트 컨벤션 강제

Agent tool로 서브에이전트를 디스패치할 때, **프롬프트에 반드시 아래 컨벤션 블록을 포함**한다.

> 이유: 서브에이전트는 프로젝트 `.claude/CLAUDE.md`를 자동으로 읽지 않는다. 프롬프트에 핵심만 명시해야 준수한다.

### 디스패치 시 필수 포함 블록

```
## 프로젝트 컨벤션 (필수 준수)

`.claude/CLAUDE.md` 및 `.claude/rules/` 레이어별 파일을 읽고 준수한다.

핵심 규칙:
1. API → UseCase → Repository 레이어 단방향. 우회 금지.
2. BaseRepository 메서드만 사용: `create(dict)`, `update(obj, dict)`, `get_by()`, `get_list_with_pagination(filters=)`
3. UseCase에서 `session` 직접 사용 금지 (IntegrityError flush 제외)
4. 스키마: `BaseSchema` 상속 필수 (pydantic.BaseModel 직접 상속 금지)
5. 외부 노출 식별자: `public_id` (UUID). `id` (BigInt) 노출 금지.
6. `.env` 파일 절대 열지 않는다.
```

$ARGUMENTS
