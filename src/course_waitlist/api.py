"""HTTP API for the single-offering course waitlist service."""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from .domain import CourseOfferingService, OperationResult


class EnrollmentRequest(BaseModel):
    learner_id: str = Field(min_length=1, max_length=100)
    prerequisite_satisfied: bool


class DropRequest(BaseModel):
    learner_id: str = Field(min_length=1, max_length=100)


class OperationResponse(BaseModel):
    outcome: str
    detail: str
    promoted_learner_id: Optional[str] = None


def _response(result: OperationResult) -> OperationResponse:
    return OperationResponse(**result.__dict__)


def create_app(service: Optional[CourseOfferingService] = None) -> FastAPI:
    app = FastAPI(title="Course Waitlist Service", version="0.1.0")
    app.state.offering_service = service or CourseOfferingService()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/offering")
    def get_offering() -> dict[str, object]:
        return app.state.offering_service.snapshot()

    @app.post("/offering/enroll", response_model=OperationResponse)
    def enroll(request: EnrollmentRequest) -> OperationResponse:
        result = app.state.offering_service.enroll(
            request.learner_id, request.prerequisite_satisfied
        )
        if result.outcome == "invalid_request":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.detail)
        return _response(result)

    @app.post("/offering/drop", response_model=OperationResponse)
    def drop(request: DropRequest) -> OperationResponse:
        result = app.state.offering_service.drop(request.learner_id)
        if result.outcome == "invalid_request":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.detail)
        return _response(result)

    return app


app = create_app()
