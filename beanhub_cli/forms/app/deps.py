import json
import typing
import urllib.parse

import yaml
from fastapi import Depends
from pydantic import parse_obj_as
from starlette.requests import Request
from starlette.templating import Jinja2Templates
from starlette_wtf.csrf import csrf_token

from . import constants
from ..data_types.form import FormDoc
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
    templates = Jinja2Templates(directory=constants.PACKAGE_DIR / "app" / "templates")
    # Notice: This will override the original `url_for` provided by Jinja2Templates
    templates.env.globals["url_for"] = url_for
    templates.env.globals["request"] = request
    templates.env.globals["get_flashed_messages"] = get_flashed_messages
    templates.env.globals["csrf_token"] = lambda: csrf_token(request)
    templates.env.globals["constants"] = constants
    templates.env.globals["settings"] = settings
    return templates


def get_form_doc() -> FormDoc | None:
    form_doc_path = settings.BEANCOUNT_DIR / ".beanhub" / "forms.yaml"
    if not form_doc_path.exists():
        return
    with form_doc_path.open("rt") as fo:
        payload = yaml.safe_load(fo)
        return parse_obj_as(FormDoc, payload)


Jinja2TemplatesDep = typing.Annotated[Jinja2Templates, Depends(get_templates)]
FlashDep = typing.Annotated[typing.Callable[[str, str, bool], None], Depends(get_flash)]
UrlForDep = typing.Annotated[typing.Callable, Depends(get_url_for)]
FormDocDep = typing.Annotated[FormDoc | None, Depends(get_form_doc)]
