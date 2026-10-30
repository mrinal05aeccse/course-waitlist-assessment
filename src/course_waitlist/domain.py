"""In-memory domain logic for exactly one course offering."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from threading import RLock


@dataclass(frozen=True)
class WaitlistEntry:
    learner_id: str


@dataclass(frozen=True)
class OperationResult:
    outcome: str
    detail: str
    promoted_learner_id: str | None = None


class CourseOfferingService:
    """Owns the state transitions for one offering.

    Every public operation is executed while holding one re-entrant lock.  This
    makes the capacity check and resulting enrollment/waitlist mutation atomic
    for this in-memory process.
    """

    def __init__(self, offering_id: str = "CS-101-2026", capacity: int = 2) -> None:
        if not offering_id.strip():
            raise ValueError("offering_id must not be blank")
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self.offering_id = offering_id
        self.capacity = capacity
        self._enrolled: set[str] = set()
        self._waitlist: deque[WaitlistEntry] = deque()
        # In a real system this comes from the learner-record/prerequisite service.
        self._prerequisite_status: dict[str, bool] = {}
        self._lock = RLock()

    def enroll(self, learner_id: str, prerequisite_satisfied: bool) -> OperationResult:
        """Enroll a learner or, when full, add an eligible learner once to FIFO queue."""
        learner_id = learner_id.strip()
        if not learner_id:
            return OperationResult("invalid_request", "learner_id must not be blank")

        with self._lock:
            if learner_id in self._enrolled:
                return OperationResult("already_enrolled", "learner is already enrolled")
            if self._is_waitlisted(learner_id):
                return OperationResult("already_waitlisted", "learner is already on the waitlist")

            self._prerequisite_status[learner_id] = prerequisite_satisfied
            if not prerequisite_satisfied:
                return OperationResult(
                    "prerequisite_not_met", "learner does not satisfy the prerequisite"
                )
            if len(self._enrolled) < self.capacity:
                self._enrolled.add(learner_id)
                return OperationResult("enrolled", "learner enrolled successfully")

            self._waitlist.append(WaitlistEntry(learner_id))
            return OperationResult("waitlisted", "course is full; learner added to waitlist")

    def drop(self, learner_id: str) -> OperationResult:
        """Drop an enrolled learner and promote the next currently eligible learner."""
        learner_id = learner_id.strip()
        if not learner_id:
            return OperationResult("invalid_request", "learner_id must not be blank")

        with self._lock:
            if learner_id not in self._enrolled:
                return OperationResult("not_enrolled", "learner is not enrolled in this offering")

            self._enrolled.remove(learner_id)
            promoted = self._promote_next_eligible()
            if promoted is None:
                return OperationResult("dropped", "learner dropped; no eligible learner was waiting")
            return OperationResult(
                "dropped_and_promoted",
                "learner dropped and earliest eligible waitlisted learner promoted",
                promoted,
            )

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                "offering_id": self.offering_id,
                "capacity": self.capacity,
                "available_seats": self.capacity - len(self._enrolled),
                "enrolled_learner_ids": sorted(self._enrolled),
                "waitlisted_learner_ids": [entry.learner_id for entry in self._waitlist],
            }

    def _is_waitlisted(self, learner_id: str) -> bool:
        return any(entry.learner_id == learner_id for entry in self._waitlist)

    def _promote_next_eligible(self) -> str | None:
        # Policy: a learner who is no longer eligible at promotion time is
        # removed (skipped), and the next FIFO entry is considered.
        while self._waitlist and len(self._enrolled) < self.capacity:
            entry = self._waitlist.popleft()
            if self._prerequisite_status.get(entry.learner_id, False):
                self._enrolled.add(entry.learner_id)
                return entry.learner_id
        return None
