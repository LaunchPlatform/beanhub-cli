from http import HTTPStatus
from typing import Any
from typing import Optional
from typing import Union

import httpx

from ... import errors
from ...client import AuthenticatedClient
from ...client import Client
from ...models.create_sync_batch_response import CreateSyncBatchResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    username: str,
    repo_name: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/v1/repos/{username}/{repo_name}/connect/sync_batches",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[CreateSyncBatchResponse, HTTPValidationError]]:
    if response.status_code == 201:
        response_201 = CreateSyncBatchResponse.from_dict(response.json())

        return response_201
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[CreateSyncBatchResponse, HTTPValidationError]]:
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
) -> Response[Union[CreateSyncBatchResponse, HTTPValidationError]]:
    """Create a sync batch

    Args:
        username (str):
        repo_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CreateSyncBatchResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        username=username,
        repo_name=repo_name,
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
) -> Optional[Union[CreateSyncBatchResponse, HTTPValidationError]]:
    """Create a sync batch

    Args:
        username (str):
        repo_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CreateSyncBatchResponse, HTTPValidationError]
    """

    return sync_detailed(
        username=username,
        repo_name=repo_name,
        client=client,
    ).parsed


async def asyncio_detailed(
    username: str,
    repo_name: str,
    *,
    client: AuthenticatedClient,
) -> Response[Union[CreateSyncBatchResponse, HTTPValidationError]]:
    """Create a sync batch

    Args:
        username (str):
        repo_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CreateSyncBatchResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        username=username,
        repo_name=repo_name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    username: str,
    repo_name: str,
    *,
    client: AuthenticatedClient,
) -> Optional[Union[CreateSyncBatchResponse, HTTPValidationError]]:
    """Create a sync batch

    Args:
        username (str):
        repo_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CreateSyncBatchResponse, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            username=username,
            repo_name=repo_name,
            client=client,
        )
    ).parsed
