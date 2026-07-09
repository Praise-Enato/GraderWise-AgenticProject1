"""Tests for the grade-of-record + content hashing.

The eng review accepted X4/OV#8: a prize competition needs a re-derivable,
defensible answer to "why did I get this score?". Stochastic ensemble + a
server-side model that drifts week to week means nothing is reproducible unless
the exact inputs are pinned. This module pins them: a content hash of the
graded inputs, an ensemble-reconciled cache key, and a GradeOfRecord capturing
model/temperatures/seeds/prompt hash + the canonical per-criterion result.

Also resolves OV#6: the cache key includes temperature and run index, so
distinct ensemble samples do NOT collapse to one cached value, while an
identical re-submission still hits cache. Pure Python, TDD.
"""
import pytest

from backend.src import grade_record as GR


_RUBRIC = [{"criteria": "Market", "max_points": 8, "description": "sizing"}]
_SUB = "We target 2.3 million smallholder farmers."


def test_content_hash_is_deterministic():
    assert GR.content_hash(_RUBRIC, _SUB) == GR.content_hash(_RUBRIC, _SUB)


def test_content_hash_changes_with_submission_or_rubric():
    base = GR.content_hash(_RUBRIC, _SUB)
    assert GR.content_hash(_RUBRIC, _SUB + " more") != base
    assert GR.content_hash([{"criteria": "Risk", "max_points": 5, "description": "x"}], _SUB) != base


def test_cache_key_distinguishes_temperature_and_run_index():
    h = GR.content_hash(_RUBRIC, _SUB)
    k0 = GR.cache_key(h, model="deepseek-chat", temperature=0.0, run_index=0)
    k1 = GR.cache_key(h, model="deepseek-chat", temperature=0.3, run_index=0)
    k2 = GR.cache_key(h, model="deepseek-chat", temperature=0.0, run_index=1)
    assert len({k0, k1, k2}) == 3               # ensemble runs never collapse
    assert k0 == GR.cache_key(h, model="deepseek-chat", temperature=0.0, run_index=0)  # stable


def test_cache_key_same_inputs_same_model_hits_cache():
    h = GR.content_hash(_RUBRIC, _SUB)
    assert GR.cache_key(h, "m", 0.0, 0) == GR.cache_key(h, "m", 0.0, 0)


def test_grade_of_record_round_trips_through_dict():
    rec = GR.GradeOfRecord(
        input_hash="abc123",
        model="deepseek-chat",
        temperatures=[0.0, 0.3, 0.6],
        seeds=[1, 2, 3],
        prompt_hash="ph1",
        per_criterion={"Market": 6.0},
        total=6.0,
        created_at="2026-07-07T00:00:00Z",
    )
    d = rec.to_dict()
    assert d["input_hash"] == "abc123"
    assert d["temperatures"] == [0.0, 0.3, 0.6]
    assert GR.GradeOfRecord.from_dict(d) == rec
