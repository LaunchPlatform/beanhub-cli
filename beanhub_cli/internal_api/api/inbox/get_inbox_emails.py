from http import HTTPStatus
from typing import Any
from typing import Optional
from typing import Union

import httpx

from ... import errors
from ...client import AuthenticatedClient
from ...client import Client
from ...models.get_inbox_email_response import GetInboxEmailResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response
from ...types import UNSET
from ...types import Unset


def _get_kwargs(
    username: str,
    repo_name: str,
    *,
    cursor: Union[None, Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_cursor: Union[None, Unset, str]
    if isinstance(cursor, Unset):
        json_cursor = UNSET
    else:
        json_cursor = cursor
    params["cursor"] = json_cursor

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/v1/repos/{username}/{repo_name}/inbox/emails",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetInboxEmailResponse, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = GetInboxEmailResponse.from_dict(response.json())

        return response_200
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[GetInboxEmailResponse, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    username: str,
    repo_name: str,
    *,
    client: AuthenticatedClient,
    cursor: Union[None, Unset, str] = UNSET,
) -> Response[Union[GetInboxEmailResponse, HTTPValidationError]]:
    """Get inbox emails

    Args:
        username (str):
        repo_name (str):
        cursor (Union[None, Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetInboxEmailResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        username=username,
        repo_name=repo_name,
        cursor=cursor,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    username: str,
    repo_name: str,
    *,
    client: AuthenticatedClient,
    cursor: Union[None, Unset, str] = UNSET,
) -> Optional[Union[GetInboxEmailResponse, HTTPValidationError]]:
    """Get inbox emails

    Args:
        username (str):
        repo_name (str):
        cursor (Union[None, Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetInboxEmailResponse, HTTPValidationError]
    """

    return sync_detailed(
        username=username,
        repo_name=repo_name,
        client=client,
        cursor=cursor,
    ).parsed


async def asyncio_detailed(
    username: str,
    repo_name: str,
    *,
    client: AuthenticatedClient,
    cursor: Union[None, Unset, str] = UNSET,
) -> Response[Union[GetInboxEmailResponse, HTTPValidationError]]:
    """Get inbox emails

    Args:
        username (str):
        repo_name (str):
        cursor (Union[None, Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetInboxEmailResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        username=username,
        repo_name=repo_name,
        cursor=cursor,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    username: str,
    repo_name: str,
    *,
    client: AuthenticatedClient,
    cursor: Union[None, Unset, str] = UNSET,
) -> Optional[Union[GetInboxEmailResponse, HTTPValidationError]]:
    """Get inbox emails

    Args:
        username (str):
        repo_name (str):
        cursor (Union[None, Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetInboxEmailResponse, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            username=username,
            repo_name=repo_name,
            client=client,
            cursor=cursor,
        )
    ).parsed
