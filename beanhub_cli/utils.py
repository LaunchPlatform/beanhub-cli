import logging
import sys


# TODO: make this a decorator instead
def check_imports(
    logger: logging.Logger, module_names: list[str], required_extras: list[str]
):
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
