import pandas as pd
from frontend.python.app import format_value, history_to_dataframe

def test_format_value_handles_none():
    assert format_value(None) == "n/a"
    assert format_value(None, " km") == "n/a"

def test_format_value_handles_int():
    assert format_value(10) == "10"
    assert format_value(1000, " L") == "1,000 L"

def test_format_value_handles_float():
    assert format_value(10.5) == "10.50"
    assert format_value(1000.123, " km") == "1,000.12 km"

def test_history_to_dataframe_empty():
    df = history_to_dataframe([])
    assert isinstance(df, pd.DataFrame)
    assert df.empty

def test_history_to_dataframe_with_data():
    history = [
        {"id": 2, "refueled_at": "2026-04-12T10:00:00", "distance_since_previous_km": 150},
        {"id": 1, "refueled_at": "2026-04-10T10:00:00", "distance_since_previous_km": None},
    ]
    df = history_to_dataframe(history)
    assert len(df) == 2
    # Verify sorting by date
    assert df.iloc[0]["id"] == 1
    assert df.iloc[1]["id"] == 2
    # Verify NA distance filled with 0
    assert df.iloc[0]["distance_since_previous_km"] == 0
    assert df.iloc[1]["distance_since_previous_km"] == 150
