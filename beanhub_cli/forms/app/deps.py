import io
import json
import pathlib
import typing
import urllib.parse
from importlib.metadata import version

import yaml.parser
import yaml.scanner
from beanhub_forms.data_types.form import FormDoc
from fastapi import Depends
from fastapi import status
from fastapi.exceptions import HTTPException
from starlette.requests import Request
from starlette.templating import Jinja2Templates
from starlette_wtf.csrf import csrf_token

from . import constants
from ..validator import format_loc
from .settings import settings


def get_url_for(request: Request) -> typing.Callable:
    def url_for(
        name: str,
        _query: typing.Optional[typing.Mapping[str, typing.Any]] = None,
        **path_params: typing.Any,
    ) -> str:
        url = request.url_for(name, **path_params)
        if _query:
            query_str = urllib.parse.urlencode(_query)
            return f"{url}?{query_str}"
        return url

    return url_for


def get_flash(request: Request) -> typing.Callable[[str, str], None]:
    def flash(message: str, category: str, markup_safe=False):
        messages: list[dict] = json.loads(
            request.session.setdefault("messages", json.dumps([]))
        )
        messages.append(
            dict(category=category, message=message, markup_safe=markup_safe)
        )
        request.session["messages"] = json.dumps(messages)

    return flash


def get_flashed_messages(
    request: Request,
) -> typing.Callable[[], typing.List[typing.Tuple[str, str]]]:
    def get_flashed_messages_func() -> typing.List[typing.Tuple[str, str]]:
        messages: typing.List[typing.Tuple[str, str]] = json.loads(
            request.session.setdefault("messages", json.dumps([]))
        )
        request.session["messages"] = json.dumps([])
        return messages

    return get_flashed_messages_func


def get_templates(
    request: Request,
    get_flashed_messages: typing.Callable[[], list[tuple[str, str]]] = Depends(
        get_flashed_messages
    ),
    url_for: typing.Callable = Depends(get_url_for),
) -> Jinja2Templates:
    templates = Jinja2Templates(
        directory=constants.FORMS_PACKAGE_DIR / "app" / "templates"
    )
    # Notice: This will override the original `url_for` provided by Jinja2Templates
    templates.env.globals["url_for"] = url_for
    templates.env.globals["request"] = request
    templates.env.globals["get_flashed_messages"] = get_flashed_messages
    templates.env.globals["csrf_token"] = lambda: csrf_token(request)
    templates.env.globals["constants"] = constants
    templates.env.globals["settings"] = settings
    templates.env.globals["beanhub_cli_version"] = version("beanhub-cli")
    templates.env.globals["beanhub_forms_version"] = version("beanhub-forms")

    templates.env.filters["format_loc"] = format_loc
    return templates


def get_raw_form_doc() -> typing.Optional[tuple[pathlib.Path, str]]:
    form_doc_path = settings.BEANCOUNT_DIR / ".beanhub" / "forms.yaml"
    if not form_doc_path.exists():
        return
    with form_doc_path.open("rt") as fo:
        payload = fo.read()
    return form_doc_path, payload


def get_form_doc(
    raw_form_doc: tuple[pathlib.Path, str] = Depends(get_raw_form_doc),
    get_url_for: typing.Callable = Depends(get_url_for),
) -> typing.Optional[FormDoc]:
    if raw_form_doc is None:
        return
    try:
        _, raw_doc = raw_form_doc
        return FormDoc.model_validate(yaml.safe_load(io.StringIO(raw_doc)))
    except (ValueError, yaml.parser.ParserError, yaml.scanner.ScannerError):
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": str(get_url_for("form_doc_errors"))},
        )


def get_sample_form_doc() -> str:
    return (constants.DATA_DIR / "sample_forms_doc.yaml").read_text()


Jinja2TemplatesDep = typing.Annotated[Jinja2Templates, Depends(get_templates)]
FlashDep = typing.Annotated[typing.Callable[[str, str, bool], None], Depends(get_flash)]
UrlForDep = typing.Annotated[typing.Callable, Depends(get_url_for)]
RawFormDocDep = typing.Annotated[
    typing.Optional[tuple[pathlib.Path, dict]], Depends(get_raw_form_doc)
]
FormDocDep = typing.Annotated[typing.Optional[FormDoc], Depends(get_form_doc)]
SampleFormDocDep = typing.Annotated[str, Depends(get_sample_form_doc)]
