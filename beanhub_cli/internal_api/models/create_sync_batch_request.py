from typing import Any
from typing import TypeVar
from typing import Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET
from ..types import Unset

T = TypeVar("T", bound="CreateSyncBatchRequest")


@_attrs_define
class CreateSyncBatchRequest:
    """
    Attributes:
        import_and_commit (Union[Unset, bool]): When enabled, sync all items in the batch first, then run a single
            import and commit to the Git repository after every item has finished syncing. Only available for Git
            repositories; Connect repositories only support syncing transactions and exporting data. Default: False.
    """

    import_and_commit: Union[Unset, bool] = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        import_and_commit = self.import_and_commit

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if import_and_commit is not UNSET:
            field_dict["import_and_commit"] = import_and_commit

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        import_and_commit = d.pop("import_and_commit", UNSET)

        create_sync_batch_request = cls(
            import_and_commit=import_and_commit,
        )

        create_sync_batch_request.additional_properties = d
        return create_sync_batch_request

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
