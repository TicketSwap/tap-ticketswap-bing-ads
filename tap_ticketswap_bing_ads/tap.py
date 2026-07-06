"""Bing Ads (Microsoft Advertising) tap class."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from singer_sdk import Tap
from singer_sdk import typing as th

from tap_ticketswap_bing_ads import streams

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

if TYPE_CHECKING:
    from tap_ticketswap_bing_ads.client import BingAdsStream


class TapBingAds(Tap):
    """Singer tap for Microsoft (Bing) Ads."""

    name = "tap-ticketswap-bing-ads"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "developer_token",
            th.StringType(nullable=False),
            required=True,
            secret=True,
            title="Developer Token",
            description="Microsoft Advertising developer token.",
        ),
        th.Property(
            "oauth_client_id",
            th.StringType(nullable=False),
            required=True,
            secret=True,
            title="OAuth Client ID",
            description="Azure application (client) id used for OAuth.",
        ),
        th.Property(
            "oauth_client_secret",
            th.StringType(nullable=False),
            required=True,
            secret=True,
            title="OAuth Client Secret",
            description="Azure application client secret used for OAuth.",
        ),
        th.Property(
            "refresh_token",
            th.StringType(nullable=False),
            required=True,
            secret=True,
            title="Refresh Token",
            description="OAuth refresh token used to obtain access tokens.",
        ),
        th.Property(
            "customer_id",
            th.StringType(nullable=False),
            required=True,
            title="Customer ID",
            description="Microsoft Advertising manager (customer) id.",
        ),
        th.Property(
            "account_ids",
            th.StringType(nullable=False),
            required=True,
            title="Account IDs",
            description="Comma-separated list of account ids to sync.",
        ),
        th.Property(
            "start_date",
            th.DateTimeType(nullable=False),
            required=True,
            title="Start Date",
            description="Earliest report date to sync, in YYYY-MM-DDTHH:MM:SSZ format.",
        ),
        th.Property(
            "conversion_window",
            th.IntegerType,
            default=30,
            title="Conversion Window",
            description="Number of days before the bookmark to re-sync on each run.",
        ),
        th.Property(
            "report_max_days",
            th.IntegerType,
            default=30,
            title="Report Window Size",
            description="Maximum number of days requested per report call.",
        ),
    ).to_dict()

    @override
    def discover_streams(self) -> list[BingAdsStream]:
        """Return a list of discovered streams."""
        return [
            streams.CampaignsStream(self),
            streams.CampaignPerformanceReportStream(self),
        ]


if __name__ == "__main__":
    TapBingAds.cli()
