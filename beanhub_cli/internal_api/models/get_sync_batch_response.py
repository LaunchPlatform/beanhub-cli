from typing import Any
from typing import cast
from typing import TYPE_CHECKING
from typing import TypeVar
from typing import Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.sync_batch_state import SyncBatchState
from ..types import UNSET
from ..types import Unset

if TYPE_CHECKING:
    from ..models.sync_data import SyncData


T = TypeVar("T", bound="GetSyncBatchResponse")


@_attrs_define
class GetSyncBatchResponse:
    """
    Attributes:
        id (UUID): Sync batch ID.
        import_and_commit (bool): Whether this batch was created with import and commit enabled. When true, the batch
            runs a single import and commit to the Git repository after all items finish syncing.
        state (SyncBatchState):
        syncs (list['SyncData']): Per-item sync status for each Plaid item in the batch.
        all_syncs_succeeded (Union[None, Unset, bool]): Whether every item sync in the batch completed without failure.
            Set when the batch reaches a terminal state. Null while the batch is still in progress.
        error_message (Union[None, Unset, str]): Error message when batch import and commit failed.
    """

    id: UUID
    import_and_commit: bool
    state: SyncBatchState
    syncs: list["SyncData"]
    all_syncs_succeeded: Union[None, Unset, bool] = UNSET
    error_message: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        import_and_commit = self.import_and_commit

        state = self.state.value

        syncs = []
        for syncs_item_data in self.syncs:
            syncs_item = syncs_item_data.to_dict()
            syncs.append(syncs_item)

        all_syncs_succeeded: Union[None, Unset, bool]
        if isinstance(self.all_syncs_succeeded, Unset):
            all_syncs_succeeded = UNSET
        else:
            all_syncs_succeeded = self.all_syncs_succeeded

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
                "import_and_commit": import_and_commit,
                "state": state,
                "syncs": syncs,
            }
        )
        if all_syncs_succeeded is not UNSET:
            field_dict["all_syncs_succeeded"] = all_syncs_succeeded
        if error_message is not UNSET:
            field_dict["error_message"] = error_message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.sync_data import SyncData

        d = src_dict.copy()
        id = UUID(d.pop("id"))

        import_and_commit = d.pop("import_and_commit")

        state = SyncBatchState(d.pop("state"))

        syncs = []
        _syncs = d.pop("syncs")
        for syncs_item_data in _syncs:
            syncs_item = SyncData.from_dict(syncs_item_data)

            syncs.append(syncs_item)

        def _parse_all_syncs_succeeded(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        all_syncs_succeeded = _parse_all_syncs_succeeded(
            d.pop("all_syncs_succeeded", UNSET)
        )

        def _parse_error_message(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        error_message = _parse_error_message(d.pop("error_message", UNSET))

        get_sync_batch_response = cls(
            id=id,
            import_and_commit=import_and_commit,
            state=state,
            syncs=syncs,
            all_syncs_succeeded=all_syncs_succeeded,
            error_message=error_message,
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
