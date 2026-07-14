from __future__ import annotations

from watch.models import Target, TargetUpdate
from watch.storage import JsonStore


class TargetNotFoundError(LookupError):
    pass


class TargetAlreadyExistsError(ValueError):
    pass


class TargetService:
    def __init__(self, store: JsonStore) -> None:
        self._store = store

    def create(self, target: Target) -> Target:
        try:
            self._store.create_target(target)
        except FileExistsError as exc:
            raise TargetAlreadyExistsError(target.target_id) from exc
        return target

    def get(self, target_id: str) -> Target:
        target = self._store.get_target(target_id)
        if target is None:
            raise TargetNotFoundError(target_id)
        return target

    def list(self) -> list[Target]:
        return self._store.list_targets()

    def update(self, target_id: str, request: TargetUpdate) -> Target:
        target = request.apply_to(target_id)
        try:
            self._store.update_target(target)
        except FileNotFoundError as exc:
            raise TargetNotFoundError(target_id) from exc
        return target
