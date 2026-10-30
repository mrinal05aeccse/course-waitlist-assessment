# Course Registration Rubric — Self-Assessment

> The referenced scorecard was not present in the supplied (empty) repository. This evidence-based self-assessment maps directly to the stated acceptance criteria; it intentionally does not invent point values or claim a final evaluator score.

| Criterion | Self-assessment | Evidence |
| --- | --- | --- |
| 1. Available-capacity enrollment and prerequisite rule | Met | `test_enrollment_succeeds_when_capacity_is_available`; `test_prerequisite_failure_neither_enrolls_nor_waitlists` |
| 2. Full capacity, one FIFO waitlist record, duplicate safety | Met | `test_full_course_waitlists_eligible_learner_once`; domain duplicate guards |
| 3. Drop promotes earliest eligible learner | Met | `test_drop_promotes_earliest_eligible_waitlisted_learner_fifo` |
| 4. Ineligible learner not enrolled/promoted; policy documented | Met | Rejection at entry plus stale-entry removal test; documented in `docs/design-specification.md` |
| 5. Invalid requests and duplicate drops preserve state | Met | `test_invalid_and_repeated_drops_preserve_state` |
| 6. Focused test coverage and concurrency | Met | Eight automated tests, including a two-thread final-seat contention test |
| 7. AI-use record and verification | Met | `docs/ai-use-record.md`, with decisions, rejected scope, and test evidence |
| Required design/setup/risk documentation | Met | `README.md`, `docs/design-specification.md`, and `docs/limitations-and-risks.md` |

## Verification status

`python -m pytest -q` completed successfully: **8 passed**. `python -m compileall -q src tests` also completed successfully. The local Docker image could not be built in this environment because Docker Desktop's Linux daemon was not running; this is the only unverified execution path.
