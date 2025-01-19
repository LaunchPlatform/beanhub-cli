from typing import Any
from typing import TYPE_CHECKING
from typing import TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.sync_data import SyncData


T = TypeVar("T", bound="GetSyncBatchResponse")


@_attrs_define
class GetSyncBatchResponse:
    """
    Attributes:
        id (UUID):
        syncs (list['SyncData']):
    """

    id: UUID
    syncs: list["SyncData"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        syncs = []
        for syncs_item_data in self.syncs:
            syncs_item = syncs_item_data.to_dict()
            syncs.append(syncs_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "syncs": syncs,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.sync_data import SyncData

        d = src_dict.copy()
        id = UUID(d.pop("id"))

        syncs = []
        _syncs = d.pop("syncs")
        for syncs_item_data in _syncs:
            syncs_item = SyncData.from_dict(syncs_item_data)

            syncs.append(syncs_item)

        get_sync_batch_response = cls(
            id=id,
            syncs=syncs,
        )

        get_sync_batch_response.additional_properties = d
        return get_sync_batch_response

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
