import io
import logging
import pathlib
import typing

import yaml.parser
import yaml.scanner
from beancount_black.formatter import Formatter
from beancount_parser.parser import make_parser
from beanhub_forms.data_types.form import FormDoc
from beanhub_forms.data_types.form import OperationType
from beanhub_forms.form import make_custom_form
from beanhub_forms.processor import process_form
from beanhub_forms.processor import ProcessError
from beanhub_forms.processor import RenderError
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from starlette_wtf import StarletteForm

from . import deps
from .helpers import convert_fields_for_js
from .settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def home(
    request: Request,
    templates: deps.Jinja2TemplatesDep,
    form_doc: deps.FormDocDep,
    sample_form_doc: deps.SampleFormDocDep,
):
    return templates.TemplateResponse(
        "home.html",
        dict(
            request=request,
            form_doc=form_doc,
            sample_form_doc=sample_form_doc,
        ),
    )


@router.api_route("/form/{form_name}", methods=["GET", "POST"])
async def submit_form(
    request: Request,
    templates: deps.Jinja2TemplatesDep,
    flash: deps.FlashDep,
    form_doc: deps.FormDocDep,
    form_name: str,
) -> Response:
    if form_doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    forms = {form.name: form for form in form_doc.forms}
    form_schema = forms.get(form_name)
    if form_schema is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    CustomForm = make_custom_form(
        form_schema=form_schema,
        # TODO: supply values for auto-complete to work
        accounts=[],
        currencies=[],
        files=[],
        form_base=StarletteForm,
    )
    form = await CustomForm.from_formdata(request)
    errors: list[str] = []
    if await form.validate_on_submit():
        form_data = form.data.copy()
        del form_data["csrf_token"]
        logger.info("Processing form %s ...", form_schema.name)
        try:
            updated_files: set[pathlib.Path] = set()
            file_updates = process_form(
                form_schema=form_schema,
                form_data=form_data,
                beancount_dir=settings.BEANCOUNT_DIR,
            )
            # TODO: add preview mode
            # TODO: we can combine updates for the same file to speed up a bit if we
            #       have to
            for file_update in file_updates:
                file_path = pathlib.Path(file_update.file)
                file_path.parent.mkdir(exist_ok=True, parents=True)
                if file_update.type == OperationType.append:
                    with open(file_update.file, "at") as fo:
                        fo.write(file_update.content)
                    updated_files.add(file_path)
                else:
                    raise ValueError(f"Unsupported operation type {file_update.type}")
            parser = make_parser()
            formatter = Formatter()
            for updated_file in updated_files:
                tree = parser.parse(updated_file.read_text())
                output_file = io.StringIO()
                formatter.format(tree, output_file)
                updated_file.write_text(output_file.getvalue())
        except ProcessError as exc:
            errors.extend(exc.errors)
        except RenderError as exc:
            errors.append(exc.message)
        flash("Submitted form successfully", "success")
    fields = convert_fields_for_js(form=form, form_schema=form_schema)
    display_name = form_schema.name
    if form_schema.display_name is not None:
        display_name = form_schema.display_name
    return templates.TemplateResponse(
        "form.html",
        dict(
            request=request,
            form_schema=form_schema,
            display_name=display_name,
            form=form,
            fields=fields,
            errors=errors,
        ),
    )


@router.get("/errors")
def form_doc_errors(
    request: Request,
    templates: deps.Jinja2TemplatesDep,
    raw_form_doc: deps.RawFormDocDep,
    url_for: deps.UrlForDep,
) -> Response:
    if raw_form_doc is None:
        return RedirectResponse(url_for("home"))
    doc_path, raw_doc = raw_form_doc

    valid_doc = False
    yaml_error: typing.Optional[yaml.parser.ParserError] = None
    validation_error: typing.Optional[ValidationError] = None
    value_error: typing.Optional[ValueError] = None
    try:
        FormDoc.model_validate(yaml.safe_load(io.StringIO(raw_doc)))
        valid_doc = True
    except (yaml.parser.ParserError, yaml.scanner.ScannerError) as exc:
        yaml_error = exc
    except ValidationError as exc:
        validation_error = exc
    except ValueError as exc:
        value_error = exc

    return templates.TemplateResponse(
        "errors.html",
        dict(
            request=request,
            doc_path=doc_path,
            validation_error=validation_error,
            value_error=value_error,
            yaml_error=yaml_error,
            valid_doc=valid_doc,
        ),
    )


@router.post("/create-sample-doc")
def create_sample_doc(sample_form_doc: deps.SampleFormDocDep) -> dict:
    form_doc_path = settings.BEANCOUNT_DIR / ".beanhub" / "forms.yaml"
    if form_doc_path.exists():
        return dict(code="already-exists")
    form_doc_path.parent.mkdir(parents=True, exist_ok=True)
    form_doc_path.write_text(sample_form_doc)
    return dict(code="ok")
