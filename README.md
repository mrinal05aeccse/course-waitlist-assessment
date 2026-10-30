# Course Waitlist Assessment

A deliberately small FastAPI service that implements enrollment, dropping, and FIFO waitlist promotion for **one course offering**. It is an AI-assisted engineering assessment submission, not a complete registration platform.

## Quick start

Requires Python 3.9+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
uvicorn course_waitlist.api:app --reload
```

The API runs on `http://127.0.0.1:8000`; interactive documentation is at `/docs`.

Example requests:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/offering/enroll -ContentType application/json -Body '{"learner_id":"learner-1","prerequisite_satisfied":true}'
Invoke-RestMethod -Method Get http://127.0.0.1:8000/offering
```

## Docker

```powershell
docker build -t course-waitlist-service .
docker run --rm -p 8000:8000 course-waitlist-service
```

See [docs/design-specification.md](docs/design-specification.md), [docs/ai-use-record.md](docs/ai-use-record.md), [docs/limitations-and-risks.md](docs/limitations-and-risks.md), and [the self-assessment scorecard](Course-Registration-Rubric-Score.md) for the assessment deliverables.
