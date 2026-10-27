"""Standard Meltano SDK tap tests, run against the Bing Ads API.

Syncs the last three days and needs the ``TAP_TICKETSWAP_BING_ADS_*`` credentials
in the environment.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from singer_sdk.testing import SuiteConfig, get_tap_test_class

from tap_ticketswap_bing_ads.tap import TapBingAds

TestTapBingAds = get_tap_test_class(
    tap_class=TapBingAds,
    config={
        "customer_id": "169953123",
        "account_ids": "180053963",
        "start_date": (datetime.now(timezone.utc) - timedelta(days=3)).strftime(
            "%Y-%m-%dT00:00:00Z"
        ),
        "conversion_window": 0,
    },
    suite_config=SuiteConfig(ignore_no_records=True),
)
