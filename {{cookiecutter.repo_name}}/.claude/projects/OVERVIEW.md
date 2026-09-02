# OVERVIEW

> 코드 변경이 스펙과 어긋나면 이 문서를 동시 갱신한다.

## 서비스

| APP_SERVICE | 용도 | 라우터 |
|-------------|------|--------|
| `main` | 사용자 API | `app/domain/main/main_router.py` |
| `backoffice` | 어드민 API | `app/domain/backoffice/backoffice_router.py` |
| `job` | EventBridge 구동 배치 | `app/domain/job/scheduler/runner.py` |

## 테이블

| prefix | 도메인 | 테이블 |
|--------|--------|--------|
| `user_` | 사용자 | `user_users`, `user_roles`, `user_users_roles` |
| `admn_` | 어드민 | `admn_admins`, `admn_audit_logs` |
| `comn_` | 공통 | `comn_file_uploads`, `comn_notification_templates`, `comn_sms_verifications` |
| `job_` | 배치 | `job_results` |

## 환경변수

`.env.example` 참조. 운영(dev/prod)에서는 AWS Secrets Manager(`{{cookiecutter.aws_secret_prefix}}-{env}-env`)에서 로드.

## 에러코드

`app/core/enum/response_message.py`
