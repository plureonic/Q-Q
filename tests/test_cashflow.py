import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import cashflow


def test_calculate_summary_with_recurring_and_one_time(tmp_path, monkeypatch):
    data_file = tmp_path / "cashflow_data.json"
    monkeypatch.setattr(cashflow, "DATA_FILE", data_file)

    data = {
        "transactions": [
            {
                "id": "1",
                "description": "Salary",
                "amount": 3000,
                "type": "inflow",
                "recurrence": "recurring",
                "category": "income",
                "start_month": "2024-01",
                "end_month": None,
                "month": None,
            },
            {
                "id": "2",
                "description": "Rent",
                "amount": 1200,
                "type": "outflow",
                "recurrence": "recurring",
                "category": "housing",
                "start_month": "2024-01",
                "end_month": None,
                "month": None,
            },
            {
                "id": "3",
                "description": "Vacation",
                "amount": 500,
                "type": "outflow",
                "recurrence": "one-time",
                "category": "fun",
                "month": "2024-02",
                "start_month": None,
                "end_month": None,
            },
        ]
    }
    data_file.write_text(json.dumps(data))

    summary = cashflow.calculate_summary(data, "2024-02", opening_balance=200)

    assert summary["month"] == "2024-02"
    assert summary["inflows"] == 3000
    assert summary["outflows"] == 1700
    assert summary["net"] == 1300
    assert summary["closing_balance"] == 1500
    assert len(summary["transactions"]) == 3


def test_is_active_in_month():
    recurring = {
        "recurrence": "recurring",
        "start_month": "2024-01",
        "end_month": "2024-03",
        "month": None,
    }
    one_time = {"recurrence": "one-time", "month": "2024-02", "start_month": None, "end_month": None}

    assert cashflow.is_active_in_month(recurring, "2024-02")
    assert not cashflow.is_active_in_month(recurring, "2024-04")
    assert cashflow.is_active_in_month(one_time, "2024-02")
    assert not cashflow.is_active_in_month(one_time, "2024-03")
