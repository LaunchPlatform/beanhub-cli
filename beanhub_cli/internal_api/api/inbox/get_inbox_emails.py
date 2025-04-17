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
    page: Union[Unset, int] = 0,
    limit: Union[Unset, int] = 50,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["page"] = page

    params["limit"] = limit

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
    page: Union[Unset, int] = 0,
    limit: Union[Unset, int] = 50,
) -> Response[Union[GetInboxEmailResponse, HTTPValidationError]]:
    """Get inbox emails

    Args:
        username (str):
        repo_name (str):
        page (Union[Unset, int]): Current page Default: 0.
        limit (Union[Unset, int]): Limit of item number in the page Default: 50.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetInboxEmailResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        username=username,
        repo_name=repo_name,
        page=page,
        limit=limit,
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
    page: Union[Unset, int] = 0,
    limit: Union[Unset, int] = 50,
) -> Optional[Union[GetInboxEmailResponse, HTTPValidationError]]:
    """Get inbox emails

    Args:
        username (str):
        repo_name (str):
        page (Union[Unset, int]): Current page Default: 0.
        limit (Union[Unset, int]): Limit of item number in the page Default: 50.

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
        page=page,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    username: str,
    repo_name: str,
    *,
    client: AuthenticatedClient,
    page: Union[Unset, int] = 0,
    limit: Union[Unset, int] = 50,
) -> Response[Union[GetInboxEmailResponse, HTTPValidationError]]:
    """Get inbox emails

    Args:
        username (str):
        repo_name (str):
        page (Union[Unset, int]): Current page Default: 0.
        limit (Union[Unset, int]): Limit of item number in the page Default: 50.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetInboxEmailResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        username=username,
        repo_name=repo_name,
        page=page,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    username: str,
    repo_name: str,
    *,
    client: AuthenticatedClient,
    page: Union[Unset, int] = 0,
    limit: Union[Unset, int] = 50,
) -> Optional[Union[GetInboxEmailResponse, HTTPValidationError]]:
    """Get inbox emails

    Args:
        username (str):
        repo_name (str):
        page (Union[Unset, int]): Current page Default: 0.
        limit (Union[Unset, int]): Limit of item number in the page Default: 50.

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
            page=page,
            limit=limit,
        )
    ).parsed
