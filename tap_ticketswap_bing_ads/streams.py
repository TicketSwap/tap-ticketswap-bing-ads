"""Stream type classes for tap-ticketswap-bing-ads."""

from __future__ import annotations

import csv
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from bingads.v13.reporting import ReportingDownloadParameters, ReportingServiceManager

from tap_ticketswap_bing_ads import schemas
from tap_ticketswap_bing_ads.client import BingAdsStream

if TYPE_CHECKING:
    from collections.abc import Iterable

    from singer_sdk.helpers.types import Context

# CampaignTypes to request; mirrors the set synced by the previous tap.
_CAMPAIGN_TYPES = "Search Shopping DynamicSearchAds PerformanceMax Audience"


class CampaignsStream(BingAdsStream):
    """Campaigns for each configured account (full table)."""

    name = "campaigns"
    service_name = "CampaignManagementService"
    primary_keys: ClassVar[tuple[str, ...]] = ("Id",)
    replication_key = None
    schema = schemas.CAMPAIGNS

    def get_records(self, context: Context | None) -> Iterable[dict[str, Any]]:  # noqa: ARG002
        """Yield every campaign across all configured accounts."""
        for account_id in self.account_ids:
            client = self.service_client(account_id)
            self.logger.info("Fetching campaigns for account %s", account_id)
            response = client.GetCampaignsByAccountId(
                AccountId=account_id,
                CampaignType=_CAMPAIGN_TYPES,
            )
            campaigns = getattr(response, "Campaign", None) or []
            for campaign in campaigns:
                yield {
                    "Id": campaign.Id,
                    "Name": campaign.Name,
                    "Status": str(campaign.Status) if campaign.Status is not None else None,
                }


class CampaignPerformanceReportStream(BingAdsStream):
    """Daily campaign performance metrics (incremental on ``TimePeriod``)."""

    name = "campaign_performance_report"
    service_name = "ReportingService"
    primary_keys: ClassVar[tuple[str, ...]] = ()
    replication_key = "TimePeriod"
    is_sorted = False
    schema = schemas.CAMPAIGN_PERFORMANCE_REPORT

    #: Report columns to request, in output order.
    report_columns: ClassVar[tuple[str, ...]] = (
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
    )

    def get_records(self, context: Context | None) -> Iterable[dict[str, Any]]:
        """Yield report rows per account, windowed over the sync date range."""
        window_days = int(self.config.get("report_max_days", 30))
        for account_id in self.account_ids:
            start, end = self._date_range(context)
            self.logger.info(
                "Syncing %s for account %s between %s and %s",
                self.name,
                account_id,
                start.date(),
                end.date(),
            )
            manager = ReportingServiceManager(
                authorization_data=self.authorization_data(account_id),
                poll_interval_in_milliseconds=5000,
            )
            window_start = start
            while window_start <= end:
                window_end = min(window_start + timedelta(days=window_days), end)
                yield from self._download_window(manager, account_id, window_start, window_end)
                window_start = window_end + timedelta(days=1)

    def _date_range(self, context: Context | None) -> tuple[datetime, datetime]:
        """Return the (start, end) range to request, applying the conversion window."""
        conversion_window = int(self.config.get("conversion_window", 30))
        start = self.get_starting_timestamp(context)
        if start is None:
            start = datetime.fromisoformat(self.config["start_date"])
        start = start - timedelta(days=conversion_window)
        # Report through yesterday; today's data is incomplete.
        end = datetime.now(tz=timezone.utc) - timedelta(days=1)
        return min(start, end), end

    def _download_window(
        self,
        manager: ReportingServiceManager,
        account_id: str,
        start: datetime,
        end: datetime,
    ) -> Iterable[dict[str, Any]]:
        """Submit, download and parse a single report window."""
        report_request = self._build_report_request(account_id, start, end)
        with tempfile.TemporaryDirectory() as tmp_dir:
            parameters = ReportingDownloadParameters(
                report_request=report_request,
                result_file_directory=tmp_dir,
                result_file_name="report.csv",
                overwrite_result_file=True,
                timeout_in_milliseconds=3_600_000,
            )
            result_path = manager.download_file(parameters)
            if not result_path:
                self.logger.info(
                    "No %s data for account %s between %s and %s",
                    self.name,
                    account_id,
                    start.date(),
                    end.date(),
                )
                return
            with Path(result_path).open(encoding="utf-8-sig", newline="") as report_file:
                for row in csv.DictReader(report_file):
                    yield {column: row.get(column) for column in self.report_columns}

    def _build_report_request(self, account_id: str, start: datetime, end: datetime) -> Any:
        """Build a ``CampaignPerformanceReportRequest`` for the given window."""
        client = self.service_client(account_id)
        report_request = client.factory.create("CampaignPerformanceReportRequest")
        report_request.Aggregation = "Daily"
        report_request.Format = "Csv"
        report_request.ReturnOnlyCompleteData = False
        report_request.ExcludeReportHeader = True
        report_request.ExcludeReportFooter = True

        scope = client.factory.create("AccountThroughCampaignReportScope")
        scope.AccountIds = {"long": [account_id]}
        scope.Campaigns = None
        report_request.Scope = scope

        columns = client.factory.create("ArrayOfCampaignPerformanceReportColumn")
        columns.CampaignPerformanceReportColumn.append(list(self.report_columns))
        report_request.Columns = columns

        report_request.Time = self._build_report_time(client, start, end)
        return report_request

    @staticmethod
    def _build_report_time(client: Any, start: datetime, end: datetime) -> Any:
        """Build the ``ReportTime`` custom date range for the request."""
        report_time = client.factory.create("ReportTime")
        report_time.PredefinedTime = None
        report_time.ReportTimeZone = "GreenwichMeanTimeDublinEdinburghLisbonLondon"

        start_date = client.factory.create("Date")
        start_date.Day, start_date.Month, start_date.Year = start.day, start.month, start.year
        end_date = client.factory.create("Date")
        end_date.Day, end_date.Month, end_date.Year = end.day, end.month, end.year

        report_time.CustomDateRangeStart = start_date
        report_time.CustomDateRangeEnd = end_date
        return report_time
