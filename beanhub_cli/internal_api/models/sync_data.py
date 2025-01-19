from typing import Any
from typing import cast
from typing import TYPE_CHECKING
from typing import TypeVar
from typing import Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.plaid_item_sync_state import PlaidItemSyncState
from ..types import UNSET
from ..types import Unset

if TYPE_CHECKING:
    from ..models.item_data import ItemData


T = TypeVar("T", bound="SyncData")


@_attrs_define
class SyncData:
    """
    Attributes:
        id (str):
        state (PlaidItemSyncState):
        item (ItemData):
        error_message (Union[None, Unset, str]):
    """

    id: str
    state: PlaidItemSyncState
    item: "ItemData"
    error_message: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        state = self.state.value

        item = self.item.to_dict()

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
                "item": item,
            }
        )
        if error_message is not UNSET:
            field_dict["error_message"] = error_message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.item_data import ItemData

        d = src_dict.copy()
        id = d.pop("id")

        state = PlaidItemSyncState(d.pop("state"))

        item = ItemData.from_dict(d.pop("item"))

        def _parse_error_message(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        error_message = _parse_error_message(d.pop("error_message", UNSET))

        sync_data = cls(
            id=id,
            state=state,
            item=item,
            error_message=error_message,
        )

        sync_data.additional_properties = d
        return sync_data

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
