from typing import Any
from typing import cast
from typing import TypeVar
from typing import Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.inbox_dump_request_state import InboxDumpRequestState
from ..types import UNSET
from ..types import Unset

T = TypeVar("T", bound="GetInboxDumpRequestResponse")


@_attrs_define
class GetInboxDumpRequestResponse:
    """
    Attributes:
        id (UUID):
        state (InboxDumpRequestState):
        encryption_key (Union[None, Unset, str]):
        download_url (Union[None, Unset, str]):
        error_message (Union[None, Unset, str]):
    """

    id: UUID
    state: InboxDumpRequestState
    encryption_key: Union[None, Unset, str] = UNSET
    download_url: Union[None, Unset, str] = UNSET
    error_message: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        state = self.state.value

        encryption_key: Union[None, Unset, str]
        if isinstance(self.encryption_key, Unset):
            encryption_key = UNSET
        else:
            encryption_key = self.encryption_key

        download_url: Union[None, Unset, str]
        if isinstance(self.download_url, Unset):
            download_url = UNSET
        else:
            download_url = self.download_url

        error_message: Union[None, Unset, str]
        if isinstance(self.error_message, Unset):
            error_message = UNSET
        else:
            error_message = self.error_message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "state": state,
            }
        )
        if encryption_key is not UNSET:
            field_dict["encryption_key"] = encryption_key
        if download_url is not UNSET:
            field_dict["download_url"] = download_url
        if error_message is not UNSET:
            field_dict["error_message"] = error_message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        id = UUID(d.pop("id"))

        state = InboxDumpRequestState(d.pop("state"))

        def _parse_encryption_key(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        encryption_key = _parse_encryption_key(d.pop("encryption_key", UNSET))

        def _parse_download_url(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        download_url = _parse_download_url(d.pop("download_url", UNSET))

        def _parse_error_message(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        error_message = _parse_error_message(d.pop("error_message", UNSET))

        get_inbox_dump_request_response = cls(
            id=id,
            state=state,
            encryption_key=encryption_key,
            download_url=download_url,
            error_message=error_message,
        )

        get_inbox_dump_request_response.additional_properties = d
        return get_inbox_dump_request_response

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
