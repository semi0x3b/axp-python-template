# 도메인 용어

> 새 식별자(enum·컬럼·API·변수)를 만들기 전에 여기부터 확인한다. 동의어를 새로 만들지 않는다.

| 용어 | 의미 | 코드 표기 |
|------|------|----------|
| public_id | 외부 노출용 UUID 식별자 | `public_id: UUID` |
| id | 내부 BigInt PK / FK | `id: int` |
| soft delete | `deleted_at` 마킹 삭제 | `SoftDeleteMixin` |
| job | EventBridge가 구동하는 배치 작업 | `JOB_REGISTRY` |
