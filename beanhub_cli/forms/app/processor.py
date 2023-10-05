import functools
import logging
import pathlib

from jinja2.sandbox import SandboxedEnvironment

from beanhub_forms.data_types.form import FormSchema
from beanhub_forms.data_types.form import OperationType
from .settings import settings

jinja_env = SandboxedEnvironment()


def render(which: str, template: str, form_data: dict) -> str:
    try:
        return jinja_env.from_string(template).render(**form_data)
    except Exception as exc:
        raise RenderError(which=which, original_exc=exc)


class RenderError(RuntimeError):
    def __init__(self, which: str, original_exc: Exception):
        self.original_exc = original_exc
        super().__init__(f"Failed to render {which} with error: {original_exc}")

    @property
    def message(self) -> str:
        return self.args[0]


class ProcessError(RuntimeError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Process error")


def process_form(form_schema: FormSchema, form_data: dict) -> set[pathlib.Path]:
    logger = logging.getLogger(__name__)
    errors: list[str] = []
    updated_files: set[pathlib.Path] = set()
    render_func = functools.partial(render, form_data=form_data)

    for i, operation in enumerate(form_schema.operations):
        op_name = f"operations[{i}]"
        file_name = render_func(which=f"{op_name}.file", template=operation.file)
        file_path = settings.BEANCOUNT_DIR / file_name
        if not file_path.parts or ".." in file_path.parts:
            errors.append(f"Invalid path {file_name!r}")
            continue
        # Ensure the file path is still inside the beancount dir
        abs_file_path = file_path.absolute()
        if not abs_file_path.is_relative_to(settings.BEANCOUNT_DIR):
            errors.append(f"Invalid path {file_name!r}")
            continue
        text = (
            render_func(which=f"{op_name}.content", template=operation.content) + "\n"
        )
        if operation.type == OperationType.append:
            logger.info("Operation %s appends text to %s", i, file_name)
            with abs_file_path.open(mode="at") as fo:
                fo.write(text)
            updated_files.add(abs_file_path)
        else:
            raise ValueError(f"Unsupported type {operation.type.value}")
    if errors:
        raise ProcessError(errors=errors)
    return updated_files
