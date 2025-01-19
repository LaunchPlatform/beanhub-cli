from typing import Any
from typing import TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.repository_type import RepositoryType

T = TypeVar("T", bound="Repository")


@_attrs_define
class Repository:
    """
    Attributes:
        username (str):
        name (str):
        type_ (RepositoryType):
        public (bool):
        active (bool):
    """

    username: str
    name: str
    type_: RepositoryType
    public: bool
    active: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        username = self.username

        name = self.name

        type_ = self.type_.value

        public = self.public

        active = self.active

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "username": username,
                "name": name,
                "type": type_,
                "public": public,
                "active": active,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        username = d.pop("username")

        name = d.pop("name")

        type_ = RepositoryType(d.pop("type"))

        public = d.pop("public")

        active = d.pop("active")

        repository = cls(
            username=username,
            name=name,
            type_=type_,
            public=public,
            active=active,
        )

        repository.additional_properties = d
        return repository

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
