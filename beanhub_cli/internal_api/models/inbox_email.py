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
    from ..models.inbox_email_headers import InboxEmailHeaders


T = TypeVar("T", bound="InboxEmail")


@_attrs_define
class InboxEmail:
    """
    Attributes:
        id (str):
        message_id (str):
        headers (InboxEmailHeaders):
        subject (str):
        from_addresses (list[str]):
        recipients (list[str]):
        tags (Union[None, Unset, list[str]]):
    """

    id: str
    message_id: str
    headers: "InboxEmailHeaders"
    subject: str
    from_addresses: list[str]
    recipients: list[str]
    tags: Union[None, Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        message_id = self.message_id

        headers = self.headers.to_dict()

        subject = self.subject

        from_addresses = self.from_addresses

        recipients = self.recipients

        tags: Union[None, Unset, list[str]]
        if isinstance(self.tags, Unset):
            tags = UNSET
        elif isinstance(self.tags, list):
            tags = self.tags

        else:
            tags = self.tags

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "message_id": message_id,
                "headers": headers,
                "subject": subject,
                "from_addresses": from_addresses,
                "recipients": recipients,
            }
        )
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.inbox_email_headers import InboxEmailHeaders

        d = src_dict.copy()
        id = d.pop("id")

        message_id = d.pop("message_id")

        headers = InboxEmailHeaders.from_dict(d.pop("headers"))

        subject = d.pop("subject")

        from_addresses = cast(list[str], d.pop("from_addresses"))

        recipients = cast(list[str], d.pop("recipients"))

        def _parse_tags(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tags_type_0 = cast(list[str], data)

                return tags_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        tags = _parse_tags(d.pop("tags", UNSET))

        inbox_email = cls(
            id=id,
            message_id=message_id,
            headers=headers,
            subject=subject,
            from_addresses=from_addresses,
            recipients=recipients,
            tags=tags,
        )

        inbox_email.additional_properties = d
        return inbox_email

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
