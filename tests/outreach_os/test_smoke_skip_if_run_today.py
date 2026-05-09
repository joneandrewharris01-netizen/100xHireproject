import pytest

from agents.outreach_os import last_run


@pytest.mark.smoke
def test_marker_round_trip(tmp_repo_root):
    last_run.write("revops", new_leads=3, errors=0)
    assert last_run.ran_today("revops") is True

    marker = last_run.marker_path("pe")
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text('{"date": "2020-01-01", "finished_at": "2020-01-01T00:00:00", "new_leads": 0, "errors": 0}')
    assert last_run.ran_today("pe") is False
