ARG BASE_IMAGE={{cookiecutter.container_prefix}}-base
FROM ${BASE_IMAGE}

WORKDIR /app

# 소스코드 복사
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini ./

# 환경변수
ARG APP_VERSION=0.0.1
ENV APP_VERSION=${APP_VERSION}

ARG APP_SERVICE=all
ENV APP_SERVICE=${APP_SERVICE}

ARG PORT=8000
ENV PORT=${PORT}
EXPOSE ${PORT}

# 헬스체크
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT}/healthz || exit 1

# 실행
CMD ["sh", "-c", "uvicorn app.asgi:app --host 0.0.0.0 --port $PORT"]
