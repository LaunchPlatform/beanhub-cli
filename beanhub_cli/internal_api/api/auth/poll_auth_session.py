from http import HTTPStatus
from typing import Any
from typing import Optional
from typing import Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient
from ...client import Client
from ...models.auth_session_not_ready_response import AuthSessionNotReadyResponse
from ...models.auth_session_poll_response import AuthSessionPollResponse
from ...models.generic_error import GenericError
from ...models.http_validation_error import HTTPValidationError
from ...types import Response
from ...types import UNSET


def _get_kwargs(
    auth_session_id: UUID,
    *,
    secret_token: str,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["secret_token"] = secret_token

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/v1/auth/sessions/{auth_session_id}/poll",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        AuthSessionNotReadyResponse,
        AuthSessionPollResponse,
        GenericError,
        HTTPValidationError,
    ]
]:
    if response.status_code == 200:
        response_200 = AuthSessionPollResponse.from_dict(response.json())

        return response_200
    if response.status_code == 202:
        response_202 = AuthSessionNotReadyResponse.from_dict(response.json())

        return response_202
    if response.status_code == 404:
        response_404 = GenericError.from_dict(response.json())

        return response_404
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        AuthSessionNotReadyResponse,
        AuthSessionPollResponse,
        GenericError,
        HTTPValidationError,
    ]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    auth_session_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    secret_token: str,
) -> Response[
    Union[
        AuthSessionNotReadyResponse,
        AuthSessionPollResponse,
        GenericError,
        HTTPValidationError,
    ]
]:
    """Poll auth session status

    Args:
        auth_session_id (UUID):
        secret_token (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AuthSessionNotReadyResponse, AuthSessionPollResponse, GenericError, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        auth_session_id=auth_session_id,
        secret_token=secret_token,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    auth_session_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    secret_token: str,
) -> Optional[
    Union[
        AuthSessionNotReadyResponse,
        AuthSessionPollResponse,
        GenericError,
        HTTPValidationError,
    ]
]:
    """Poll auth session status

    Args:
        auth_session_id (UUID):
        secret_token (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AuthSessionNotReadyResponse, AuthSessionPollResponse, GenericError, HTTPValidationError]
    """

    return sync_detailed(
        auth_session_id=auth_session_id,
        client=client,
        secret_token=secret_token,
    ).parsed


async def asyncio_detailed(
    auth_session_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    secret_token: str,
) -> Response[
    Union[
        AuthSessionNotReadyResponse,
        AuthSessionPollResponse,
        GenericError,
        HTTPValidationError,
    ]
]:
    """Poll auth session status

    Args:
        auth_session_id (UUID):
        secret_token (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AuthSessionNotReadyResponse, AuthSessionPollResponse, GenericError, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        auth_session_id=auth_session_id,
        secret_token=secret_token,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    auth_session_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    secret_token: str,
) -> Optional[
    Union[
        AuthSessionNotReadyResponse,
        AuthSessionPollResponse,
        GenericError,
        HTTPValidationError,
    ]
]:
    """Poll auth session status

    Args:
        auth_session_id (UUID):
        secret_token (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AuthSessionNotReadyResponse, AuthSessionPollResponse, GenericError, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            auth_session_id=auth_session_id,
            client=client,
            secret_token=secret_token,
        )
    ).parsed
