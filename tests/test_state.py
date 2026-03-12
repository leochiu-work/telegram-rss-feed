import json
from pathlib import Path

import pytest

from rss_bot.state import is_seeded, load_state, mark_seen, save_state, seen_guids


def test_load_state_missing_file(tmp_path):
    state = load_state(tmp_path / "nonexistent.json")
    assert state == {}


def test_load_state_existing_file(tmp_path):
    p = tmp_path / "state.json"
    p.write_text(json.dumps({"https://example.com": {"seen_guids": ["a"], "seeded": True}}))
    state = load_state(p)
    assert state["https://example.com"]["seen_guids"] == ["a"]


def test_save_state_creates_dirs(tmp_path):
    path = tmp_path / "deep" / "nested" / "state.json"
    save_state(path, {"key": "value"})
    assert path.exists()
    assert json.loads(path.read_text()) == {"key": "value"}


def test_is_seeded_false_for_new_url():
    assert is_seeded({}, "https://example.com") is False


def test_is_seeded_true_after_mark():
    state: dict = {}
    mark_seen(state, "https://example.com", ["g1"], seeded=True)
    assert is_seeded(state, "https://example.com") is True


def test_seen_guids_empty_for_new_url():
    assert seen_guids({}, "https://example.com") == set()


def test_mark_seen_adds_guids():
    state: dict = {}
    mark_seen(state, "https://example.com", ["g1", "g2"])
    assert seen_guids(state, "https://example.com") == {"g1", "g2"}


def test_mark_seen_no_duplicates():
    state: dict = {}
    mark_seen(state, "https://example.com", ["g1"])
    mark_seen(state, "https://example.com", ["g1", "g2"])
    guids = state["https://example.com"]["seen_guids"]
    assert guids.count("g1") == 1
    assert "g2" in guids


def test_mark_seen_fifo_eviction():
    state: dict = {}
    # Fill beyond 500
    initial = [f"guid-{i}" for i in range(500)]
    mark_seen(state, "url", initial)
    assert len(state["url"]["seen_guids"]) == 500

    mark_seen(state, "url", ["new-guid"])
    guids = state["url"]["seen_guids"]
    assert len(guids) == 500
    assert "guid-0" not in guids  # oldest evicted
    assert "new-guid" in guids


def test_mark_seen_updates_last_run():
    state: dict = {}
    mark_seen(state, "url", ["g1"])
    assert state["url"]["last_run"] is not None


def test_mark_seen_seeded_false_by_default():
    state: dict = {}
    mark_seen(state, "url", ["g1"])
    assert state["url"]["seeded"] is False


def test_roundtrip(tmp_path):
    path = tmp_path / "state.json"
    state: dict = {}
    mark_seen(state, "https://example.com", ["g1", "g2"], seeded=True)
    save_state(path, state)

    loaded = load_state(path)
    assert is_seeded(loaded, "https://example.com") is True
    assert seen_guids(loaded, "https://example.com") == {"g1", "g2"}
