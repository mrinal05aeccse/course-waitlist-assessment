from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from fastapi.testclient import TestClient

from course_waitlist.api import create_app
from course_waitlist.domain import CourseOfferingService, WaitlistEntry


def client(capacity: int = 2) -> TestClient:
    return TestClient(create_app(CourseOfferingService(capacity=capacity)))


def enroll(api: TestClient, learner_id: str, eligible: bool = True) -> dict:
    response = api.post(
        "/offering/enroll",
        json={"learner_id": learner_id, "prerequisite_satisfied": eligible},
    )
    assert response.status_code == 200
    return response.json()


def test_enrollment_succeeds_when_capacity_is_available() -> None:
    api = client()
    assert enroll(api, "learner-1")["outcome"] == "enrolled"
    state = api.get("/offering").json()
    assert state["enrolled_learner_ids"] == ["learner-1"]
    assert state["available_seats"] == 1


def test_full_course_waitlists_eligible_learner_once() -> None:
    api = client(capacity=1)
    enroll(api, "learner-1")
    assert enroll(api, "learner-2")["outcome"] == "waitlisted"
    assert enroll(api, "learner-2")["outcome"] == "already_waitlisted"
    assert api.get("/offering").json()["waitlisted_learner_ids"] == ["learner-2"]


def test_duplicate_enrollment_does_not_create_another_record() -> None:
    api = client()
    enroll(api, "learner-1")
    assert enroll(api, "learner-1")["outcome"] == "already_enrolled"
    assert api.get("/offering").json()["enrolled_learner_ids"] == ["learner-1"]


def test_drop_promotes_earliest_eligible_waitlisted_learner_fifo() -> None:
    api = client(capacity=1)
    enroll(api, "enrolled")
    enroll(api, "first")
    enroll(api, "second")
    response = api.post("/offering/drop", json={"learner_id": "enrolled"})
    assert response.json() == {
        "outcome": "dropped_and_promoted",
        "detail": "learner dropped and earliest eligible waitlisted learner promoted",
        "promoted_learner_id": "first",
    }
    state = api.get("/offering").json()
    assert state["enrolled_learner_ids"] == ["first"]
    assert state["waitlisted_learner_ids"] == ["second"]


def test_prerequisite_failure_neither_enrolls_nor_waitlists() -> None:
    api = client(capacity=1)
    assert enroll(api, "ineligible", eligible=False)["outcome"] == "prerequisite_not_met"
    state = api.get("/offering").json()
    assert state["enrolled_learner_ids"] == []
    assert state["waitlisted_learner_ids"] == []


def test_ineligible_entry_at_front_is_removed_then_next_eligible_is_promoted() -> None:
    service = CourseOfferingService(capacity=1)
    service.enroll("enrolled", True)
    # Simulates a prerequisite becoming invalid after a legacy/external queue entry.
    service._waitlist.extend([WaitlistEntry("stale"), WaitlistEntry("eligible")])
    service._prerequisite_status.update({"stale": False, "eligible": True})
    result = service.drop("enrolled")
    assert result.promoted_learner_id == "eligible"
    assert service.snapshot()["waitlisted_learner_ids"] == []


def test_invalid_and_repeated_drops_preserve_state() -> None:
    api = client()
    invalid = api.post("/offering/drop", json={"learner_id": "   "})
    assert invalid.status_code == 400
    missing = api.post("/offering/drop", json={"learner_id": "missing"})
    assert missing.json()["outcome"] == "not_enrolled"
    enroll(api, "learner-1")
    assert api.post("/offering/drop", json={"learner_id": "learner-1"}).json()["outcome"] == "dropped"
    repeat = api.post("/offering/drop", json={"learner_id": "learner-1"})
    assert repeat.json()["outcome"] == "not_enrolled"
    state = api.get("/offering").json()
    assert state["available_seats"] == 2
    assert state["enrolled_learner_ids"] == []


def test_concurrent_enrollment_keeps_capacity_and_records_both_requests() -> None:
    service = CourseOfferingService(capacity=1)
    start = Barrier(2)

    def submit(learner_id: str) -> str:
        start.wait()
        return service.enroll(learner_id, True).outcome

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(submit, ["learner-1", "learner-2"]))
    state = service.snapshot()
    assert sorted(outcomes) == ["enrolled", "waitlisted"]
    assert len(state["enrolled_learner_ids"]) == 1
    assert len(state["waitlisted_learner_ids"]) == 1
    assert state["available_seats"] == 0
