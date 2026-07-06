"""Tests for tap-ticketswap-bing-ads.

These exercise discovery, configuration and schema shape without hitting the
Bing Ads API, so they run in CI without credentials.
"""

from __future__ import annotations

from tap_ticketswap_bing_ads.tap import TapBingAds

SAMPLE_CONFIG = {
    "developer_token": "dummy",
    "oauth_client_id": "dummy",
    "oauth_client_secret": "dummy",
    "refresh_token": "dummy",
    "customer_id": "169953123",
    "account_ids": "180053963,180053964",
    "start_date": "2023-01-01T00:00:00Z",
}


def _tap() -> TapBingAds:
    return TapBingAds(config=SAMPLE_CONFIG, validate_config=False)


def test_discovers_expected_streams() -> None:
    """The tap exposes exactly the two streams consumed by dbt."""
    names = {stream.name for stream in _tap().discover_streams()}
    assert names == {"campaigns", "campaign_performance_report"}


def test_stream_replication() -> None:
    """Campaigns is full-table; the report is incremental on TimePeriod."""
    streams = {stream.name: stream for stream in _tap().discover_streams()}
    assert streams["campaigns"].replication_key is None
    assert streams["campaign_performance_report"].replication_key == "TimePeriod"


def test_report_schema_contains_dbt_columns() -> None:
    """The report schema declares every column the staging model reads."""
    streams = {stream.name: stream for stream in _tap().discover_streams()}
    report_props = streams["campaign_performance_report"].schema["properties"]
    expected = {
        "TimePeriod",
        "CampaignId",
        "DeviceType",
        "Network",
        "Impressions",
        "Clicks",
        "Ctr",
        "AverageCpc",
        "AverageCpm",
        "Spend",
    }
    assert expected <= set(report_props)


def test_account_ids_parsed_from_csv() -> None:
    """Comma-separated account ids are split into a list."""
    stream = next(iter(_tap().discover_streams()))
    assert stream.account_ids == ["180053963", "180053964"]


def test_post_process_coerces_types() -> None:
    """Numeric strings are cast and placeholder/empty values become None/zero."""
    streams = {stream.name: stream for stream in _tap().discover_streams()}
    stream = streams["campaign_performance_report"]
    row = stream.post_process(
        {
            "TimePeriod": "2024-01-15",
            "CampaignId": "123",
            "DeviceType": "Computer",
            "Network": "Bing",
            "Impressions": "1,234",
            "Clicks": "--",
            "Ctr": "1.50%",
            "AverageCpc": "",
            "AverageCpm": "2.5",
            "Spend": "10.00",
        }
    )
    assert row is not None
    assert row["Impressions"] == 1234
    assert row["Clicks"] == 0
    assert row["Ctr"] == 1.5
    assert row["AverageCpc"] is None
    assert row["TimePeriod"] == "2024-01-15"
    assert row["CampaignId"] == "123"
