"""Tests for the static grounding corpus.

Verifies the corpus exists, contains NO applicant/plan-specific data (leakage guard),
and that retrieval degrades gracefully to [] when the embedding model / Chroma index
is unavailable (as in CI / this sandbox).
"""
import os

from backend.src import reference_corpus as RC


def test_reference_docs_present():
    docs = RC.list_reference_docs()
    names = {os.path.basename(d) for d in docs}
    assert {"financial_credibility.md", "market_sizing.md",
            "business_plan_quality_guide.md"} <= names


def test_reference_docs_nonempty():
    for path in RC.list_reference_docs():
        with open(path, encoding="utf-8") as fh:
            assert fh.read().strip(), path


def test_no_applicant_data_leakage():
    # The corpus must be GENERIC knowledge only — never real submissions or scores.
    forbidden = [
        "jideofor", "frost flow", "lightreach", "light reach", "kachlinks",
        "mwana", "kalemie", "roland kindness", "byums rubric", "human score",
    ]
    blob = ""
    for path in RC.list_reference_docs():
        with open(path, encoding="utf-8") as fh:
            blob += fh.read().lower()
    hits = [w for w in forbidden if w in blob]
    assert not hits, f"corpus leaks applicant/plan-specific data: {hits}"


def test_load_documents_tags_source():
    docs = RC._load_reference_documents()
    assert docs, "expected reference documents to load"
    for d in docs:
        assert d.metadata.get("source", "").endswith(".md")
        assert d.page_content.strip()


def test_retrieve_is_graceful_without_corpus():
    # No ingested Chroma index in this environment -> [] not an exception.
    assert not RC.reference_corpus_available()
    assert RC.retrieve_reference_context("financial projections") == []


def test_retrieve_empty_query_returns_empty():
    assert RC.retrieve_reference_context("") == []


def test_available_never_raises_on_oserror(monkeypatch):
    # Regression for the review finding: a permission error on the listdir probe must
    # degrade to "unavailable", not propagate and crash the grade request.
    monkeypatch.setattr(RC.os.path, "isdir", lambda p: True)

    def _boom(_):
        raise PermissionError("denied")

    monkeypatch.setattr(RC.os, "listdir", _boom)
    assert RC.reference_corpus_available() is False
    assert RC.retrieve_reference_context("financials") == []  # no exception escapes
