import typing

from beancount_data.data_types import EntryUnion
from beancount_data.data_types import ValidationResult
from pydantic import BaseModel


class ResultBase(BaseModel):
    ok: bool
    error: typing.Optional[str] = None


class ExportBeancountResult(ResultBase):
    options: typing.Optional[typing.Dict[str, typing.Any]] = None
    validation_result: typing.Optional[ValidationResult] = None
    entries: typing.Optional[EntryUnion] = None


class FormatResult(ResultBase):
    pass
