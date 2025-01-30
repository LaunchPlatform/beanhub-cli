from typing import Any
from typing import TypeVar
from typing import Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET
from ..types import Unset

T = TypeVar("T", bound="CreateDumpRequestRequest")


@_attrs_define
class CreateDumpRequestRequest:
    """
    Attributes:
        public_key (str):
        output_accounts (Union[Unset, bool]):  Default: False.
    """

    public_key: str
    output_accounts: Union[Unset, bool] = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        public_key = self.public_key

        output_accounts = self.output_accounts

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "public_key": public_key,
            }
        )
        if output_accounts is not UNSET:
            field_dict["output_accounts"] = output_accounts

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        public_key = d.pop("public_key")

        output_accounts = d.pop("output_accounts", UNSET)

        create_dump_request_request = cls(
            public_key=public_key,
            output_accounts=output_accounts,
        )

        create_dump_request_request.additional_properties = d
        return create_dump_request_request

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
