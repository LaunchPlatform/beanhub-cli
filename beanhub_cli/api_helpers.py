import functools
import json
import logging
import sys
import typing


def handle_api_exception(logger: logging.Logger | None = None):
    def decorator(func: typing.Callable):
        @functools.wraps(func)
        def callee(*args, **kwargs):
            from .internal_api.errors import UnexpectedStatus
            from .internal_api.models import GenericError

            try:
                return func(*args, **kwargs)
            except UnexpectedStatus as exp:
                log = logger or logging.getLogger(__name__)
                error = None
                try:
                    error = GenericError.from_dict(json.loads(exp.content))
                except ValueError:
                    pass
                log.error(
                    "Failed to make BeanHub API call with code %s and error: %s",
                    exp.status_code,
                    error.detail if error is not None else exp.content,
                )
                sys.exit(-1)

        return callee

    return decorator


def make_auth_client(base_url: str, token: str) -> "AuthenticatedClient":
    from .internal_api.client import AuthenticatedClient

    return AuthenticatedClient(
        base_url=base_url, prefix="", auth_header_name="access-token", token=token
    )
