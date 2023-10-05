import io
import logging

from starlette_wtf import StarletteForm
from beancount_black.formatter import Formatter
from beancount_parser.parser import make_parser
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status

from . import deps
from beanhub_forms.form import make_custom_form
from .helpers import convert_fields_for_js
from .processor import process_form
from .processor import ProcessError
from .processor import RenderError

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
        form_base=StarletteForm
    )
    form = await CustomForm.from_formdata(request)
    errors: list[str] = []
    if await form.validate_on_submit():
        form_data = form.data.copy()
        del form_data["csrf_token"]
        logger.info("Processing form %s ...", form_schema.name)
        try:
            updated_files = process_form(form_schema=form_schema, form_data=form_data)
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
