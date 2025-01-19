import enum
import functools
import logging
import sys
import typing


@enum.unique
class ExtraDepsSet(enum.Enum):
    LOGIN = "LOGIN"
    CONNECT = "CONNECT"


EXTRA_DEPS: dict[ExtraDepsSet, typing.Tuple[str, ...]] = {
    ExtraDepsSet.LOGIN: ("httpx", "attrs", "dateutil", "tomli", "tomli_w"),
    ExtraDepsSet.CONNECT: (
        "httpx",
        "attrs",
        "dateutil",
        "tomli",
        "tomli_w",
        "nacl",
        "cryptography",
    ),
}


def run_check_imports(
    logger: logging.Logger,
    module_names: typing.Sequence[str],
    required_extras: list[str],
):
    logger = logger or logging.getLogger(__name__)
    missing_modules = []
    for name in module_names:
        try:
            __import__(name)
        except ImportError:
            missing_modules.append(name)
    if not missing_modules:
        return
    extras = ",".join(required_extras)
    logger.error(
        "Cannot import module %s, please ensure that you install beanhub-cli with optional deps [%s]. "
        'Like `pip install "beanhub-cli[%s]"`',
        missing_modules,
        extras,
        extras,
    )
    sys.exit(-1)


def check_imports(extra_deps_set: ExtraDepsSet, logger: logging.Logger | None = None):
    def decorator(func: typing.Callable):
        @functools.wraps(func)
        def callee(*args, **kwargs):
            run_check_imports(
                logger=logger,
                module_names=EXTRA_DEPS[extra_deps_set],
                required_extras=[extra_deps_set.value.lower()],
            )
            return func(*args, **kwargs)

        return callee

    return decorator
