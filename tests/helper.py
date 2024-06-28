import contextlib
import os
import pathlib


@contextlib.contextmanager
def switch_cwd(cwd: pathlib.Path):
    current_cwd = pathlib.Path.cwd()
    try:
        os.chdir(cwd)
        yield
    finally:
        os.chdir(current_cwd)
