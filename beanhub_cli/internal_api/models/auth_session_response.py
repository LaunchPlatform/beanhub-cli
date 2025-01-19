from typing import Any
from typing import cast
from typing import TypeVar
from typing import Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET
from ..types import Unset

T = TypeVar("T", bound="AuthSessionResponse")


@_attrs_define
class AuthSessionResponse:
    """
    Attributes:
        id (UUID):
        code (str):
        auth_url (str):
        secret_token (str):
        poll_url (Union[None, Unset, str]):
    """

    id: UUID
    code: str
    auth_url: str
    secret_token: str
    poll_url: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        code = self.code

        auth_url = self.auth_url

        secret_token = self.secret_token

        poll_url: Union[None, Unset, str]
        if isinstance(self.poll_url, Unset):
            poll_url = UNSET
        else:
            poll_url = self.poll_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "code": code,
                "auth_url": auth_url,
                "secret_token": secret_token,
            }
        )
        if poll_url is not UNSET:
            field_dict["poll_url"] = poll_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        id = UUID(d.pop("id"))

        code = d.pop("code")

        auth_url = d.pop("auth_url")

        secret_token = d.pop("secret_token")

        def _parse_poll_url(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        poll_url = _parse_poll_url(d.pop("poll_url", UNSET))

        auth_session_response = cls(
            id=id,
            code=code,
            auth_url=auth_url,
            secret_token=secret_token,
            poll_url=poll_url,
        )

        auth_session_response.additional_properties = d
        return auth_session_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
