import json
import logging
import pathlib
import subprocess
import sys

from beancount_data.data_types import EntryUnion
from beancount_data.data_types import ValidationResult
from fastapi import APIRouter
from fastapi import Request
from pydantic import TypeAdapter

from ...format import format_beancount
from ..schemes import ExportBeancountResult
from ..schemes import FormatResult

router = APIRouter()
logger = logging.getLogger(__name__)
entry_adapter = TypeAdapter(EntryUnion)


@router.get(
    "/entries",
    response_model=ExportBeancountResult,
    operation_id="list-entries",
    description="List all Beancount entries for the given Beancount file",
)
async def list_entries(
    request: Request, beancount_file: str = "main.bean"
) -> ExportBeancountResult:
    proc = subprocess.run(
        (sys.executable, "-m", "beancount_exporter.main", beancount_file),
        timeout=10,
        capture_output=True,
    )
    lines = proc.stdout.splitlines()
    result = ExportBeancountResult(
        ok=proc.returncode == 0,
        error=proc.stderr.decode("utf8"),
    )
    if proc.returncode == 0:
        result.options = json.loads(lines[0])
        result.validation_result = ValidationResult.model_validate_json(lines[2])
        result.entries = list(map(entry_adapter.validate_json, lines[4:]))
    else:
        logger.error("Failed to export entries: %s", result.error)
    return result


@router.get(
    "/format",
    response_model=FormatResult,
    operation_id="format-beancount-file",
    description="Format beancount files",
)
async def format_beancount_file(
    request: Request, beancount_file: str = "main.bean"
) -> FormatResult:
    format_beancount(filenames=[pathlib.Path(beancount_file)])
    return FormatResult(
        ok=True,
    )
