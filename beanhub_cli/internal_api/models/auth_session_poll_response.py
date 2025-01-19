from typing import Any
from typing import cast
from typing import TypeVar
from typing import Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET
from ..types import Unset

T = TypeVar("T", bound="AuthSessionPollResponse")


@_attrs_define
class AuthSessionPollResponse:
    """
    Attributes:
        token (str):
        repositories (Union[None, Unset, list[str]]):
    """

    token: str
    repositories: Union[None, Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        token = self.token

        repositories: Union[None, Unset, list[str]]
        if isinstance(self.repositories, Unset):
            repositories = UNSET
        elif isinstance(self.repositories, list):
            repositories = self.repositories

        else:
            repositories = self.repositories

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "token": token,
            }
        )
        if repositories is not UNSET:
            field_dict["repositories"] = repositories

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        token = d.pop("token")

        def _parse_repositories(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                repositories_type_0 = cast(list[str], data)

                return repositories_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        repositories = _parse_repositories(d.pop("repositories", UNSET))

        auth_session_poll_response = cls(
            token=token,
            repositories=repositories,
        )

        auth_session_poll_response.additional_properties = d
        return auth_session_poll_response

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
