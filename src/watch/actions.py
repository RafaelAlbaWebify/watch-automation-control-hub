from __future__ import annotations

from datetime import UTC, datetime

from watch.models import ActionStatus, OperationalAction
from watch.storage import JsonStore


class ActionNotFoundError(LookupError):
    pass


class InvalidActionTransitionError(ValueError):
    pass


class ActionService:
    def __init__(self, store: JsonStore) -> None:
        self._store = store

    def acknowledge(self, action_id: str) -> OperationalAction:
        action = self._require(action_id)
        if action.status == ActionStatus.RESOLVED:
            raise InvalidActionTransitionError("resolved action cannot be acknowledged")
        if action.status == ActionStatus.ACKNOWLEDGED:
            return action
        updated = action.model_copy(
            update={"status": ActionStatus.ACKNOWLEDGED, "updated_at": datetime.now(UTC)}
        )
        self._store.save_action(updated)
        return updated

    def resolve(self, action_id: str, resolution_note: str) -> OperationalAction:
        note = resolution_note.strip()
        if not note:
            raise ValueError("resolution note is required")
        action = self._require(action_id)
        if action.status == ActionStatus.RESOLVED:
            raise InvalidActionTransitionError("action is already resolved")
        updated = action.model_copy(
            update={
                "status": ActionStatus.RESOLVED,
                "resolution_note": note,
                "updated_at": datetime.now(UTC),
            }
        )
        self._store.save_action(updated)
        return updated

    def _require(self, action_id: str) -> OperationalAction:
        action = self._store.get_action(action_id)
        if action is None:
            raise ActionNotFoundError(action_id)
        return action
