from agents.outreach_os import xlsx_loader


def test_loads_all_rows(fixtures_dir):
    rows = xlsx_loader.load(fixtures_dir / "b2b_leads_10.xlsx")
    assert len(rows) == 10
    assert rows[0]["name"] == "Sarah Chen"
    assert rows[0]["title"] == "VP RevOps"
    assert rows[0]["company"] == "Acme"


def test_columns_lowercased(fixtures_dir):
    rows = xlsx_loader.load(fixtures_dir / "b2b_leads_10.xlsx")
    assert "linkedin_url" in rows[0]
