from http import HTTPStatus
from typing import Any
from typing import Optional
from typing import Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient
from ...client import Client
from ...models.get_sync_batch_response import GetSyncBatchResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    username: str,
    repo_name: str,
    sync_batch_id: UUID,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/v1/repos/{username}/{repo_name}/connect/sync_batches/{sync_batch_id}",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[GetSyncBatchResponse, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = GetSyncBatchResponse.from_dict(response.json())

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
) -> Response[Union[GetSyncBatchResponse, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    username: str,
    repo_name: str,
    sync_batch_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[Union[GetSyncBatchResponse, HTTPValidationError]]:
    """Get a sync batch

    Args:
        username (str):
        repo_name (str):
        sync_batch_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetSyncBatchResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        username=username,
        repo_name=repo_name,
        sync_batch_id=sync_batch_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    username: str,
    repo_name: str,
    sync_batch_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Optional[Union[GetSyncBatchResponse, HTTPValidationError]]:
    """Get a sync batch

    Args:
        username (str):
        repo_name (str):
        sync_batch_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetSyncBatchResponse, HTTPValidationError]
    """

    return sync_detailed(
        username=username,
        repo_name=repo_name,
        sync_batch_id=sync_batch_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    username: str,
    repo_name: str,
    sync_batch_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[Union[GetSyncBatchResponse, HTTPValidationError]]:
    """Get a sync batch

    Args:
        username (str):
        repo_name (str):
        sync_batch_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetSyncBatchResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        username=username,
        repo_name=repo_name,
        sync_batch_id=sync_batch_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    username: str,
    repo_name: str,
    sync_batch_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Optional[Union[GetSyncBatchResponse, HTTPValidationError]]:
    """Get a sync batch

    Args:
        username (str):
        repo_name (str):
        sync_batch_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetSyncBatchResponse, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            username=username,
            repo_name=repo_name,
            sync_batch_id=sync_batch_id,
            client=client,
        )
    ).parsed
