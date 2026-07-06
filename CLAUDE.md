# AGENTS.md — AI agent guide for tap-ticketswap-bing-ads

Guidance for AI agents and developers working on this Singer tap.

## Overview

- **Type**: Singer tap, built with the Meltano Singer SDK.
- **Source**: Microsoft (Bing) Ads — a SOAP API accessed via the official
  [`bingads`](https://pypi.org/project/bingads/) SDK.
- **Purpose**: Slim replacement for the legacy
  [`tap-bing-ads`](https://github.com/TicketSwap/tap-bing-ads). It extracts only
  the streams consumed by the `microsoft_ads` dbt models in
  `data-transformations`.

## Streams

| Stream | Service call | Replication key | dbt model |
|---|---|---|---|
| `campaigns` | `CampaignManagementService.GetCampaignsByAccountId` | — (full table) | `stg_microsoft_ads__campaigns` |
| `campaign_performance_report` | `ReportingService` → `CampaignPerformanceReportRequest` (Daily) | `TimePeriod` | `stg_microsoft_ads__campaign_performance` |

**Do not rename streams or fields.** Stream names must match the dbt
`source('microsoft_ads', ...)` table names, and fields are emitted in PascalCase
so the loader's lower-casing reproduces the existing warehouse columns. Adding a
column means: (1) add it to `schemas.py`, and (2) for the report, add it to
`CampaignPerformanceReportStream.report_columns`.

## Layout

```
tap_ticketswap_bing_ads/
├── tap.py       # TapBingAds: config schema + discover_streams
├── client.py    # BingAdsStream base: OAuth, AuthorizationData, ServiceClient, post_process
├── streams.py   # CampaignsStream, CampaignPerformanceReportStream
└── schemas.py   # PropertiesList schemas (dbt-used columns only)
```

## Config

Required: `developer_token`, `oauth_client_id`, `oauth_client_secret`,
`refresh_token`, `customer_id`, `account_ids` (comma-separated), `start_date`.
Optional: `conversion_window` (default 30), `report_max_days` (default 30).

Keep `config_jsonschema` in `tap.py`, the `settings` block in `meltano.yml`, and
`.env.example` in sync in the same commit.

## Development

```bash
uv sync
uv run pytest                       # no credentials needed
uv run tap-ticketswap-bing-ads --about
```

Tests in `tests/test_core.py` cover discovery, config and type coercion without
hitting the API. A real end-to-end run needs valid Microsoft Ads credentials.

## Notes

- Reporting is windowed (`report_max_days`) and re-syncs `conversion_window`
  days before the bookmark, since Bing metrics keep changing for ~30 days.
- The `_sdc_*` metadata columns (including `_sdc_received_at`, which dbt reads)
  are added by the loader, not this tap.
- SDK: https://sdk.meltano.com — check the deprecation guide before bumping
  `singer-sdk`.
