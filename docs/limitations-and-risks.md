# Limitations and follow-up risks

- State is lost on service restart and is not shared between application workers. A production implementation needs durable storage and transactional/optimistic-concurrency enforcement.
- Prerequisite status is supplied by the request in this assessment. A real integration must obtain it from an authoritative, authenticated academic-record source and define when it is re-evaluated.
- The one-process lock only protects in-process threads. Horizontal deployment needs database-backed coordination.
- This service intentionally has no authentication, authorization, audit logging, notification, deadline, or course-catalog behavior; those belong outside the specified slice.
- The stale-entry policy removes ineligible entries without a notification mechanism. A production workflow should capture a reason and notify the learner.
