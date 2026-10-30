# AI prompt and use record

## Record

No credentials, personal data, or proprietary source material were included in AI prompts.

| Engineering activity | Prompt / relevant response summary | Disposition | Files or decisions informed | Independent verification |
| --- | --- | --- | --- | --- |
| Initial solution decomposition | **Prompt:** “Implement a bounded FastAPI service for one course offering with enrollment, drop, prerequisite checks, FIFO waitlist promotion, tests, design documentation, and Docker support.” **Response summary:** proposed a lock-protected in-memory service, an explicit result model, a FIFO queue, and focused unit/API tests. | **Edited and accepted in part.** The broad decomposition was accepted. The prerequisite policy was refined to reject ineligible learners at entry and remove stale ineligible entries during promotion. | `src/course_waitlist/domain.py`, `src/course_waitlist/api.py`, test plan and this specification. | Code review checked each acceptance criterion against the service transitions; `pytest` verifies capacity, duplicate, FIFO, prerequisite, invalid/repeated-drop, and concurrency behavior. |
| Concurrency review | **Prompt:** “For an in-memory single-offering enrollment service, identify the smallest safe synchronization boundary for capacity and waitlist changes.” **Response summary:** lock the whole check-and-mutate transition, not just individual collection calls; add a simultaneous final-seat test. | **Accepted.** | `CourseOfferingService._lock`; `test_concurrent_enrollment_keeps_capacity_and_records_both_requests`. | The test starts two threads at a barrier and verifies exactly one enrollment, one waitlist result, and no capacity overrun. |

## Human review decisions

- The suggested broad registration-domain abstractions were rejected: they would exceed the one-offering scope.
- A public endpoint to mutate prerequisites was rejected because it would introduce an unrelated learner-record API. The service nevertheless rechecks stored eligibility on promotion to make the stale-entry policy explicit and testable.
- HTTP outcomes remain readable application results for duplicate requests and duplicate drops; no mutation is hidden behind an exception.

## Verification evidence

The implementation was independently checked on 2026-10-30 with:

```text
python -m pytest -q
8 passed, 1 warning

python -m compileall -q src tests
exit code 0
```

The test suite directly exercises the AI-informed locking choice and the required behavior. A local `docker build -t course-waitlist-service:local .` was also attempted, but this environment has no running Docker Desktop Linux daemon (`//./pipe/dockerDesktopLinuxEngine` was unavailable). The Dockerfile is included and its build/run commands are recorded in the README for a Docker-enabled environment.
