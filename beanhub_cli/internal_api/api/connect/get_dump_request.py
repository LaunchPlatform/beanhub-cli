from http import HTTPStatus
from typing import Any
from typing import Optional
from typing import Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient
from ...client import Client
from ...models.get_dump_request_response import GetDumpRequestResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    username: str,
    repo_name: str,
    dump_request_id: UUID,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/v1/repos/{username}/{repo_name}/connect/dumps/{dump_request_id}",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetDumpRequestResponse, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = GetDumpRequestResponse.from_dict(response.json())

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
) -> Response[Union[GetDumpRequestResponse, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    username: str,
    repo_name: str,
    dump_request_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[Union[GetDumpRequestResponse, HTTPValidationError]]:
    """Get a dump request

    Args:
        username (str):
        repo_name (str):
        dump_request_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetDumpRequestResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        username=username,
        repo_name=repo_name,
        dump_request_id=dump_request_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    username: str,
    repo_name: str,
    dump_request_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Optional[Union[GetDumpRequestResponse, HTTPValidationError]]:
    """Get a dump request

    Args:
        username (str):
        repo_name (str):
        dump_request_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetDumpRequestResponse, HTTPValidationError]
    """

    return sync_detailed(
        username=username,
        repo_name=repo_name,
        dump_request_id=dump_request_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    username: str,
    repo_name: str,
    dump_request_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[Union[GetDumpRequestResponse, HTTPValidationError]]:
    """Get a dump request

    Args:
        username (str):
        repo_name (str):
        dump_request_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetDumpRequestResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        username=username,
        repo_name=repo_name,
        dump_request_id=dump_request_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    username: str,
    repo_name: str,
    dump_request_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Optional[Union[GetDumpRequestResponse, HTTPValidationError]]:
    """Get a dump request

    Args:
        username (str):
        repo_name (str):
        dump_request_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetDumpRequestResponse, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            username=username,
            repo_name=repo_name,
            dump_request_id=dump_request_id,
            client=client,
        )
    ).parsed
