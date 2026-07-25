"""Shared fixtures.

The sample resume is deliberately *clean* — it passes every content rule — so that
a lint test can assert a specific finding by breaking exactly one thing. A fixture
that already trips three rules makes every assertion ambiguous.
"""
from __future__ import annotations

import copy
import json

import pytest

from career_docs import model

CLEAN = {
    "basics": {
        "name": "Jane Smith",
        "label": "Software Engineer | Backend · APIs",
        "email": "jane@example.com",
        "phone": "(555) 555-5555",
        "location": {"city": "Portland", "region": "OR", "countryCode": "US"},
        "profiles": [
            {"network": "GitHub", "username": "jsmith",
             "url": "https://github.com/jsmith"},
        ],
        "summary": (
            "Backend engineer with 6 years building APIs in Python and Go, "
            "across 3 production services on teams of 5 to 12 engineers."
        ),
    },
    "skills": [
        {"name": "Languages", "keywords": ["Python", "Go", "SQL"]},
        {"name": "Tools", "keywords": ["Docker", "Postgres"]},
    ],
    "work": [
        {
            "name": "Northwind",
            "position": "Senior Engineer",
            "location": "Portland, OR",
            "startDate": "2021-03",
            "highlights": [
                "Shipped 14 API endpoints backing the billing product.",
                "Cut median request latency from 400ms to 120ms.",
                "Grew the integration suite to 220 tests against a real database.",
                "Led 2 engineers through the migration to Postgres 15.",
                "Wrote the design docs for 3 subsystems still in use.",
            ],
        },
        {
            "name": "Contoso",
            "position": "Engineer",
            "startDate": "2018-06",
            "endDate": "2021-02",
            "highlights": [
                "Built an ETL pipeline moving 2M rows nightly.",
                "Replaced 4 cron jobs with a single scheduler.",
            ],
        },
    ],
    "education": [
        {
            "institution": "State University",
            "studyType": "Bachelor of Science",
            "area": "in Computer Science",
            "endDate": "2018-05",
        },
    ],
}


@pytest.fixture
def data() -> dict:
    """A fresh deep copy, so a test that mutates cannot leak into the next."""
    return copy.deepcopy(CLEAN)


def _load(tmp_path, payload: dict):
    path = tmp_path / "resume.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return model.load(path)


@pytest.fixture
def resume(tmp_path, data):
    return _load(tmp_path, data)


@pytest.fixture
def make_resume(tmp_path):
    """Load a modified resume: `make_resume(lambda d: d["basics"].pop("email"))`."""
    def _make(mutate=None) -> model.Resume:
        payload = copy.deepcopy(CLEAN)
        if mutate:
            mutate(payload)
        return _load(tmp_path, payload)
    return _make
