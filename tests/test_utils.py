import logging

import pytest
from pytest_mock import MockFixture

from beanhub_cli.utils import check_imports


def test_check_imports(mocker: MockFixture):
    logger = logging.getLogger(__name__)
    spy = mocker.spy(logger, "error")
    with pytest.raises(SystemExit) as exp:
        check_imports(
            logger=logger,
            module_names=["never_ever_exists0", "never_ever_exists1"],
            required_extras=["extras0", "extras1"],
        )
    assert exp.value.args[0] == -1
    spy.assert_called_once_with(
        "Cannot import module %s, please ensure that you install beanhub-cli with optional deps [%s]. "
        'Like `pip install "beanhub-cli[%s]"`',
        ["never_ever_exists0", "never_ever_exists1"],
        "extras0,extras1",
        "extras0,extras1",
    )


def test_check_imports_no_problem(mocker: MockFixture):
    logger = logging.getLogger(__name__)
    spy = mocker.spy(logger, "error")
    check_imports(
        logger=logger,
        module_names=["sys"],
        required_extras=["extras"],
    )
    spy.assert_not_called()
