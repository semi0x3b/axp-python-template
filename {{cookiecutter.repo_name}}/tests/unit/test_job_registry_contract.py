"""JOB_REGISTRY에 등록된 모든 job이 runner 호출 규약과 맞는지 검사.

runner는 클래스 job을 `cls(session)` 으로 생성한 뒤 `instance.method(**params)` 로 호출한다.
따라서 진입 메서드는 인스턴스 메서드여야 하며, session 외의 필수 인자를 가지면 안 된다.
(등록만 해두고 시그니처가 어긋나 운영에서 터지는 사고를 막는 계약 테스트)
"""

import importlib
import inspect

import pytest

from app.domain.job.scheduler.runner import JOB_REGISTRY, _resolve_callable


@pytest.mark.parametrize("job_name", sorted(JOB_REGISTRY))
def test_registered_job_matches_runner_call_convention(job_name: str) -> None:
    func_path = JOB_REGISTRY[job_name]["func"]
    module_path, class_or_func, method_name = _resolve_callable(func_path)
    module = importlib.import_module(module_path)

    target = getattr(module, class_or_func)

    if method_name is None:
        _assert_no_required_args(target, func_path)
        return

    # 클래스 job: __init__(session) + 인스턴스 메서드
    init_params = list(inspect.signature(target.__init__).parameters.values())[1:]
    assert len(init_params) == 1, f"{func_path}: __init__은 session 하나만 받아야 함"

    method = inspect.getattr_static(target, method_name)
    assert not isinstance(method, (classmethod, staticmethod)), f"{func_path}: runner가 인스턴스로 호출하므로 classmethod/staticmethod 금지"

    _assert_no_required_args(getattr(target, method_name), func_path, skip_self=True)


def _assert_no_required_args(func, func_path: str, skip_self: bool = False) -> None:
    params = list(inspect.signature(func).parameters.values())
    if skip_self:
        params = params[1:]
    required = [p.name for p in params if p.default is inspect.Parameter.empty and p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)]
    assert not required, f"{func_path}: params 없이 호출되므로 필수 인자 금지 (발견: {required})"
