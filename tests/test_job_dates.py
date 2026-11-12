

from datetime import datetime, timedelta, timezone

from backend.app.adzuna_client import _is_within_days


def test_recent_unix_timestamp():
    timestamp = int(
        (datetime.now(timezone.utc) - timedelta(days=2)).timestamp()
    )
    assert _is_within_days(timestamp, 7)


def test_old_unix_timestamp():
    timestamp = int(
        (datetime.now(timezone.utc) - timedelta(days=60)).timestamp()
    )
    assert not _is_within_days(timestamp, 30)


def test_recent_millisecond_timestamp():
    timestamp_ms = int(
        (datetime.now(timezone.utc) - timedelta(days=2)).timestamp() * 1000
    )
    assert _is_within_days(timestamp_ms, 7)


def test_iso_date():
    date_string = (
        datetime.now(timezone.utc) - timedelta(days=3)
    ).isoformat()
    assert _is_within_days(date_string, 7)


def test_missing_date():
    assert _is_within_days(None, 7)
