from typing import Any
from typing import cast
from typing import TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="CreateInboxDumpRequest")


@_attrs_define
class CreateInboxDumpRequest:
    """
    Attributes:
        public_key (str):
        email_ids (list[str]):
    """

    public_key: str
    email_ids: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        public_key = self.public_key

        email_ids = self.email_ids

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "public_key": public_key,
                "email_ids": email_ids,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        public_key = d.pop("public_key")

        email_ids = cast(list[str], d.pop("email_ids"))

        create_inbox_dump_request = cls(
            public_key=public_key,
            email_ids=email_ids,
        )

        create_inbox_dump_request.additional_properties = d
        return create_inbox_dump_request

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
