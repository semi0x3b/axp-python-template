from enum import StrEnum


class Environment(StrEnum):
    """실행 환경."""

    local = "local"
    development = "dev"
    production = "prod"
