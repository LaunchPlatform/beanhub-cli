from typing import Any
from typing import cast
from typing import TypeVar
from typing import Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ItemData")


@_attrs_define
class ItemData:
    """
    Attributes:
        id (str):
        institution_name (Union[None, str]):
    """

    id: str
    institution_name: Union[None, str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        institution_name: Union[None, str]
        institution_name = self.institution_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "institution_name": institution_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("id")

        def _parse_institution_name(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        institution_name = _parse_institution_name(d.pop("institution_name"))

        item_data = cls(
            id=id,
            institution_name=institution_name,
        )

        item_data.additional_properties = d
        return item_data

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
