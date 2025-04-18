from typing import Any
from typing import cast
from typing import TYPE_CHECKING
from typing import TypeVar
from typing import Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET
from ..types import Unset

if TYPE_CHECKING:
    from ..models.inbox_email import InboxEmail


T = TypeVar("T", bound="GetInboxEmailResponse")


@_attrs_define
class GetInboxEmailResponse:
    """
    Attributes:
        emails (list['InboxEmail']):
        cursor (Union[None, Unset, str]):
    """

    emails: list["InboxEmail"]
    cursor: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        emails = []
        for emails_item_data in self.emails:
            emails_item = emails_item_data.to_dict()
            emails.append(emails_item)

        cursor: Union[None, Unset, str]
        if isinstance(self.cursor, Unset):
            cursor = UNSET
        else:
            cursor = self.cursor

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "emails": emails,
            }
        )
        if cursor is not UNSET:
            field_dict["cursor"] = cursor

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.inbox_email import InboxEmail

        d = src_dict.copy()
        emails = []
        _emails = d.pop("emails")
        for emails_item_data in _emails:
            emails_item = InboxEmail.from_dict(emails_item_data)

            emails.append(emails_item)

        def _parse_cursor(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        cursor = _parse_cursor(d.pop("cursor", UNSET))

        get_inbox_email_response = cls(
            emails=emails,
            cursor=cursor,
        )

        get_inbox_email_response.additional_properties = d
        return get_inbox_email_response

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
