# Design specification — Course Waitlist slice

## Service boundary

This service owns enrollment state for exactly one offering, `CS-101-2026` (configurable only by constructing the service). It exposes four HTTP endpoints:

| Method and path | Purpose |
| --- | --- |
| `GET /health` | Liveness check |
| `GET /offering` | Read-only snapshot of capacity, enrollment, and queue |
| `POST /offering/enroll` | Enroll or waitlist a learner |
| `POST /offering/drop` | Drop an enrolled learner and attempt promotion |

Enrollment requests contain `learner_id` and `prerequisite_satisfied`. In production, the boolean would be supplied by an authoritative learner-record/prerequisite service; it is a deliberately explicit input in this small assessment service.

## Assumptions and policy

1. There is one offering and one fixed positive integer capacity.
2. A learner satisfies the prerequisite only when `prerequisite_satisfied` is `true`.
3. An ineligible learner is neither enrolled nor added to the waitlist. The result is `prerequisite_not_met`.
4. Eligibility is checked again when a queued learner reaches the front. If that learner is then ineligible, the service **skips and removes** the entry, then considers the next entry. This is the documented stale-entry policy; it prevents a seat from being blocked indefinitely.
5. A learner can occur at most once across the enrollment set and waitlist. An existing enrollment takes precedence over the prerequisite flag in a duplicate request and returns `already_enrolled`.

## Invariants

- `0 <= enrolled_count <= capacity` after every operation.
- An enrolled learner is not waitlisted, and a waitlisted learner is unique.
- Waitlist order is FIFO among entries still eligible at promotion time.
- Dropping a non-enrolled learner changes no state.
- Invalid blank IDs change no state.

## State transitions

`enroll` validates the ID, rejects duplicate enrollment/waitlisting, records the supplied eligibility, then:

- rejects an ineligible learner;
- enrolls an eligible learner if `enrolled_count < capacity`; or
- appends the eligible learner to the tail of the waitlist.

`drop` validates the ID and only removes an existing enrollment. It then removes queue entries in order until it finds an eligible learner, promotes that learner into the newly open seat, or exhausts the queue.

The response uses explicit outcomes rather than treating expected state conflicts as server errors: `enrolled`, `waitlisted`, `already_enrolled`, `already_waitlisted`, `prerequisite_not_met`, `dropped`, `dropped_and_promoted`, and `not_enrolled`. Schema-invalid request bodies receive FastAPI's 422 response; domain-invalid blank IDs receive 400.

## Concurrency and persistence approach

The store is intentionally in-memory. A single `RLock` covers each complete state transition, so the check for remaining capacity and the mutation are atomic in one process. The concurrency test proves two competing requests for the final seat yield one enrollment and one waitlist entry.

This lock does not coordinate multiple processes or survive restart. A production successor should put the same invariants in a transactional database operation (row-level lock or optimistic retry) and persist the queue sequence number. That is outside this bounded assessment.

## Tradeoffs

The API uses a boolean eligibility input to avoid introducing identity, transcript, catalog, or policy-engine scope. A set is used for enrollment because ordering is not meaningful; snapshots sort enrolled IDs solely for deterministic API/test output. A deque preserves FIFO queue order efficiently.
