import io
import logging
import pathlib

from beancount_black.formatter import Formatter
from beancount_parser.parser import make_parser
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
):
    return templates.TemplateResponse(
        "home.html",
        dict(
            request=request,
            form_doc=form_doc,
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
    return templates.TemplateResponse(
        "form.html",
        dict(
            request=request,
            form_schema=form_schema,
            form=form,
            fields=fields,
            errors=errors,
        ),
    )
